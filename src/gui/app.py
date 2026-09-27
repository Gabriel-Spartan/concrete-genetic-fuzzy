"""
Interfaz Gráfica de Escritorio (Desktop GUI) en Tkinter para el Sistema Difuso-Genético.
Permite evaluar mezclas personalizadas de concreto tanto en Modo Continuo (numérico)
como en Modo Lingüístico (por etiquetas difusas), cargar casos típicos predefinidos
y visualizar la estimación de resistencia (MPa) junto con la explicabilidad
de las reglas difusas activadas y los grados de pertenencia completos.
"""

import re
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np

from src.fuzzy.inference import FuzzyInferenceSystem
from src.fuzzy.membership import trapmf, trimf


# Especificación de variables de entrada con valores por defecto y límites físicos estrictos [min, max]
INPUT_SPECS = [
    ("cement", "Cemento", "kg/m³", 330.0, 102.0, 540.0),
    ("blast_furnace_slag", "Escoria de Alto Horno", "kg/m³", 0.0, 0.0, 360.0),
    ("fly_ash", "Ceniza Volante", "kg/m³", 0.0, 0.0, 200.0),
    ("water", "Agua", "kg/m³", 180.0, 120.0, 247.0),
    ("superplasticizer", "Superplastificante", "kg/m³", 0.0, 0.0, 32.0),
    ("coarse_aggregate", "Agregado Grueso", "kg/m³", 1040.0, 800.0, 1145.0),
    ("fine_aggregate", "Agregado Fino", "kg/m³", 780.0, 594.0, 992.0),
    ("age", "Edad de Curado", "días", 28.0, 1.0, 365.0),
]

VAR_BOUNDS = {cid: (min_v, max_v) for cid, _, _, _, min_v, max_v in INPUT_SPECS}

# Definición de etiquetas lingüísticas con valores representativos del núcleo (μ = 1.0)
LINGUISTIC_LABELS = {
    "cement": [
        ("Poco (~150 kg/m³)", 149.3, "poco"),
        ("Medio (~295 kg/m³)", 295.0, "medio"),
        ("Alto (~450 kg/m³)", 450.0, "alto"),
    ],
    "blast_furnace_slag": [
        ("No Aplica (0 kg/m³)", 0.0, "no_aplica"),
        ("Poco (~65 kg/m³)", 64.4, "poco"),
        ("Medio (~145 kg/m³)", 145.2, "medio"),
        ("Alto (~260 kg/m³)", 260.0, "alto"),
    ],
    "fly_ash": [
        ("No Aplica (0 kg/m³)", 0.0, "no_aplica"),
        ("Poco (~60 kg/m³)", 61.8, "poco"),
        ("Medio (~115 kg/m³)", 113.1, "medio"),
        ("Alto (~170 kg/m³)", 170.8, "alto"),
    ],
    "water": [
        ("Poco (~135 kg/m³)", 134.8, "poco"),
        ("Medio (~175 kg/m³)", 173.4, "medio"),
        ("Alto (~220 kg/m³)", 220.0, "alto"),
    ],
    "superplasticizer": [
        ("No Aplica (0 kg/m³)", 0.0, "no_aplica"),
        ("Poco (~5 kg/m³)", 5.1, "poco"),
        ("Medio (~8.5 kg/m³)", 8.4, "medio"),
        ("Alto (~20 kg/m³)", 20.0, "alto"),
    ],
    "coarse_aggregate": [
        ("Poco (~850 kg/m³)", 849.8, "poco"),
        ("Medio (~990 kg/m³)", 992.7, "medio"),
        ("Alto (~1100 kg/m³)", 1100.0, "alto"),
    ],
    "fine_aggregate": [
        ("Poco (~665 kg/m³)", 664.5, "poco"),
        ("Medio (~815 kg/m³)", 817.0, "medio"),
        ("Alto (~900 kg/m³)", 909.1, "alto"),
    ],
    "age": [
        ("Muy Temprana (~3 días)", 3.0, "muy_temprana"),
        ("Estándar (~28 días)", 28.0, "estandar"),
        ("Madura (~56 días)", 56.0, "madura"),
        ("Largo Plazo (~90 días)", 90.0, "largo_plazo"),
    ],
}

# Casos predefinidos de mezclas típicas de ingeniería civil
PRESETS = {
    "estandar": {
        "title": "Hormigón Estándar (28d)",
        "values": {
            "cement": 330.0, "blast_furnace_slag": 0.0, "fly_ash": 0.0,
            "water": 180.0, "superplasticizer": 0.0,
            "coarse_aggregate": 1040.0, "fine_aggregate": 780.0, "age": 28.0,
        },
    },
    "alta_resistencia": {
        "title": "Alta Resistencia - HPC (28d)",
        "values": {
            "cement": 450.0, "blast_furnace_slag": 120.0, "fly_ash": 0.0,
            "water": 155.0, "superplasticizer": 10.0,
            "coarse_aggregate": 980.0, "fine_aggregate": 720.0, "age": 28.0,
        },
    },
    "baja_resistencia": {
        "title": "Baja Resistencia / Pobre (28d)",
        "values": {
            "cement": 160.0, "blast_furnace_slag": 0.0, "fly_ash": 0.0,
            "water": 215.0, "superplasticizer": 0.0,
            "coarse_aggregate": 1080.0, "fine_aggregate": 820.0, "age": 28.0,
        },
    },
    "edad_temprana": {
        "title": "Desencofrado Rápido (3d)",
        "values": {
            "cement": 380.0, "blast_furnace_slag": 0.0, "fly_ash": 0.0,
            "water": 175.0, "superplasticizer": 3.0,
            "coarse_aggregate": 1020.0, "fine_aggregate": 760.0, "age": 3.0,
        },
    },
}


class ConcreteFuzzyGUI:
    """Aplicación de escritorio en Tkinter para el sistema difuso-genético."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Sistema Difuso-Genético: Estimación de Resistencia del Concreto")
        self.root.geometry("1060x740")
        self.root.minsize(960, 660)

        # Cargar el motor sintonizado del AG
        try:
            self.fis = FuzzyInferenceSystem.from_tuned()
            self.model_status = "Modelo Sintonizado con AG (Activo)"
        except Exception as e:
            self.fis = FuzzyInferenceSystem()
            self.model_status = f"Modelo Nominal Inicial (Línea Base: {e})"

        self._updating_from_combo = False
        self._updating_from_entry = False

        self._configure_styles()
        self._build_ui()
        self.load_preset("estandar")

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Header.TLabel", font=("DejaVu Sans", 14, "bold"), foreground="#0F172A")
        style.configure("SubHeader.TLabel", font=("DejaVu Sans", 9), foreground="#64748B")
        style.configure("Section.TLabelframe.Label", font=("DejaVu Sans", 10, "bold"), foreground="#1E3A8A")
        style.configure("Primary.TButton", font=("DejaVu Sans", 10, "bold"), padding=6)
        style.configure("Preset.TButton", font=("DejaVu Sans", 9), padding=4)
        style.configure("Treeview.Heading", font=("DejaVu Sans", 9, "bold"))
        style.configure("Treeview", font=("DejaVu Sans", 9), rowheight=24)

    def _build_ui(self):
        # 1. Marco superior de encabezado
        header_frame = ttk.Frame(self.root, padding="15 8 15 4")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text="Predicción Inteligente de Resistencia a Compresión del Concreto",
            style="Header.TLabel",
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            header_frame,
            text=f"Motor de Inferencia Difuso Takagi-Sugeno con Reglas PRISM y Sintonización Genética | {self.model_status}",
            style="SubHeader.TLabel",
        )
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=6)

        # 2. Contenedor principal de dos columnas
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        left_container = ttk.Frame(main_paned, width=470)
        right_container = ttk.Frame(main_paned, width=570)
        main_paned.add(left_container, weight=4)
        main_paned.add(right_container, weight=6)

        # ====================================================================
        # COLUMNA IZQUIERDA: MODO DUAL (CONTINUO / LINGÜÍSTICO) Y CASOS
        # ====================================================================
        input_tabs = ttk.Notebook(left_container)
        input_tabs.pack(fill=tk.X, padx=5, pady=(5, 4))

        # Pestaña 1: Ingreso Numérico Continuo
        tab_numeric = ttk.Frame(input_tabs, padding=8)
        input_tabs.add(tab_numeric, text=" 🔢 Valores Continuos (kg/m³, d) ")

        self.entries = {}
        for row_idx, (col_id, label_es, unit, def_val, min_v, max_v) in enumerate(INPUT_SPECS):
            lbl = ttk.Label(tab_numeric, text=f"{label_es}:", font=("DejaVu Sans", 9))
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=2)

            vcmd = (self.root.register(self._validate_keystroke), "%P", col_id)
            entry = ttk.Entry(
                tab_numeric,
                width=10,
                font=("DejaVu Sans", 9, "bold"),
                justify=tk.RIGHT,
                validate="key",
                validatecommand=vcmd,
            )
            init_str = f"{def_val:.3f}".rstrip("0").rstrip(".")
            entry.insert(0, init_str)
            entry.grid(row=row_idx, column=1, sticky=tk.E, padx=(5, 5), pady=2)
            entry.bind("<KeyRelease>", lambda event, cid=col_id: self._on_entry_changed(cid))
            entry.bind("<FocusOut>", lambda event, cid=col_id: self._on_focus_out(cid))
            self.entries[col_id] = entry

            range_hint = f"{int(min_v) if min_v.is_integer() else min_v} - {int(max_v) if max_v.is_integer() else max_v}"
            unit_lbl = ttk.Label(tab_numeric, text=f"{unit} ({range_hint})", font=("DejaVu Sans", 8), foreground="#64748B")
            unit_lbl.grid(row=row_idx, column=2, sticky=tk.W, pady=2)

        # Pestaña 2: Ingreso por Etiquetas Lingüísticas (Fuzzy Labels)
        tab_linguistic = ttk.Frame(input_tabs, padding=8)
        input_tabs.add(tab_linguistic, text=" 🏷️ Etiquetas Difusas (Cualitativo) ")

        self.combos = {}
        for row_idx, (col_id, label_es, unit, _, _, _) in enumerate(INPUT_SPECS):
            lbl = ttk.Label(tab_linguistic, text=f"{label_es}:", font=("DejaVu Sans", 9))
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=2)

            options = [desc for desc, _, _ in LINGUISTIC_LABELS[col_id]]
            combo = ttk.Combobox(tab_linguistic, values=options, state="readonly", width=22, font=("DejaVu Sans", 8))
            combo.current(0)
            combo.grid(row=row_idx, column=1, sticky=tk.W, padx=(5, 5), pady=2)
            combo.bind("<<ComboboxSelected>>", lambda event, cid=col_id: self._on_combo_selected(cid))
            self.combos[col_id] = combo

        # Marco de casos rápidos predefinidos (Presets)
        preset_group = ttk.LabelFrame(left_container, text=" Casos Típicos de Ensayo (1-Click) ", padding=6)
        preset_group.pack(fill=tk.X, padx=5, pady=6)

        for key, pinfo in PRESETS.items():
            btn = ttk.Button(
                preset_group,
                text=pinfo["title"],
                style="Preset.TButton",
                command=lambda k=key: self.load_preset(k),
            )
            btn.pack(fill=tk.X, pady=2)

        # Botones de Acción
        actions_frame = ttk.Frame(left_container, padding="5 8 5 4")
        actions_frame.pack(fill=tk.X)

        calc_btn = ttk.Button(
            actions_frame,
            text="► CALCULAR RESISTENCIA (MPa)",
            style="Primary.TButton",
            command=self.calculate_prediction,
        )
        calc_btn.pack(fill=tk.X, ipady=4)

        reset_btn = ttk.Button(actions_frame, text="Limpiar Valores", command=self.clear_fields)
        reset_btn.pack(fill=tk.X, pady=(4, 0))

        # ====================================================================
        # COLUMNA DERECHA: RESULTADOS Y EXPLICABILIDAD DIFUSA
        # ====================================================================
        result_group = ttk.LabelFrame(right_container, text=" Resistencia Estimada a Compresión ", padding=10)
        result_group.pack(fill=tk.X, padx=5, pady=5)

        self.res_val_lbl = tk.Label(
            result_group,
            text="--.-- MPa",
            font=("DejaVu Sans", 26, "bold"),
            foreground="#1E3A8A",
            bg="#F8FAFC",
            padx=10,
            pady=4,
            relief=tk.RIDGE,
        )
        self.res_val_lbl.pack(fill=tk.X, pady=3)

        details_meta_frame = ttk.Frame(result_group)
        details_meta_frame.pack(fill=tk.X, pady=(4, 0))

        self.class_badge = tk.Label(
            details_meta_frame,
            text="Clase: Sin Calcular",
            font=("DejaVu Sans", 10, "bold"),
            bg="#E2E8F0",
            fg="#1E293B",
            padx=8,
            pady=3,
        )
        self.class_badge.pack(side=tk.LEFT)

        self.wc_ratio_lbl = ttk.Label(
            details_meta_frame,
            text="Relación a/mc: --",
            font=("DejaVu Sans", 9, "bold"),
            foreground="#334155",
        )
        self.wc_ratio_lbl.pack(side=tk.RIGHT)

        self.status_rule_lbl = ttk.Label(
            result_group,
            text="Estado: Esperando cálculo...",
            font=("DejaVu Sans", 8),
            foreground="#64748B",
        )
        self.status_rule_lbl.pack(anchor=tk.W, pady=(6, 0))

        # Pestañas de Razonamiento y Reglas
        notebook = ttk.Notebook(right_container)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=6)

        # Pestaña 1: Reglas disparadas
        tab_rules = ttk.Frame(notebook, padding=6)
        notebook.add(tab_rules, text=" Reglas Disparadas (Razonamiento) ")

        cols = ("num", "weight", "consequent", "centroid", "logic")
        self.tree_rules = ttk.Treeview(tab_rules, columns=cols, show="headings", height=8)
        self.tree_rules.heading("num", text="Regla")
        self.tree_rules.heading("weight", text="Fuerza (w)")
        self.tree_rules.heading("consequent", text="Consecuente")
        self.tree_rules.heading("centroid", text="y* (MPa)")
        self.tree_rules.heading("logic", text="Condición Lógica")

        self.tree_rules.column("num", width=50, anchor=tk.CENTER)
        self.tree_rules.column("weight", width=80, anchor=tk.CENTER)
        self.tree_rules.column("consequent", width=95, anchor=tk.CENTER)
        self.tree_rules.column("centroid", width=80, anchor=tk.CENTER)
        self.tree_rules.column("logic", width=220, anchor=tk.W)

        scroll_y = ttk.Scrollbar(tab_rules, orient=tk.VERTICAL, command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=scroll_y.set)
        self.tree_rules.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Pestaña 2: Pertenencias difusas completas (Solo Lectura)
        tab_membership = ttk.Frame(notebook, padding=6)
        notebook.add(tab_membership, text=" Pertenencias Difusas (μ) ")

        self.txt_membership = tk.Text(
            tab_membership,
            wrap=tk.WORD,
            font=("Courier", 9),
            height=8,
            bg="#F8FAFC",
            state=tk.DISABLED,
        )
        scroll_m = ttk.Scrollbar(tab_membership, orient=tk.VERTICAL, command=self.txt_membership.yview)
        self.txt_membership.configure(yscrollcommand=scroll_m.set)
        self.txt_membership.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_m.pack(side=tk.RIGHT, fill=tk.Y)

    def _validate_keystroke(self, new_val: str, col_id: str) -> bool:
        """
        Valida cada pulsación de teclado en tiempo real:
        1. Rechaza letras, símbolos y caracteres especiales.
        2. Solo permite dígitos y a lo sumo un separador decimal (punto o coma).
        3. Limita a un máximo de 3 cifras decimales.
        4. Rechaza valores que superen el límite superior (max_val) de la variable.
        """
        if new_val == "":
            return True

        # Expresión regular: solo dígitos con máximo un punto/coma y hasta 3 decimales
        pattern = r"^\d*([.,]\d{0,3})?$"
        if not re.match(pattern, new_val):
            return False

        # Verificar límite superior si es un número convertible
        clean_num = new_val.replace(",", ".")
        if clean_num not in (".", ""):
            try:
                val = float(clean_num)
                max_val = VAR_BOUNDS[col_id][1]
                if val > max_val:
                    return False
            except ValueError:
                return False

        return True

    def _on_focus_out(self, col_id: str):
        """Verifica los límites inferior y superior al perder el foco y ajusta si es necesario."""
        raw = self.entries[col_id].get().strip().replace(",", ".")
        if not raw or raw == ".":
            # Restaurar valor por defecto
            def_val = next(d for c, _, _, d, _, _ in INPUT_SPECS if c == col_id)
            val_str = f"{def_val:.3f}".rstrip("0").rstrip(".")
            self.entries[col_id].delete(0, tk.END)
            self.entries[col_id].insert(0, val_str)
            self.calculate_prediction()
            return

        try:
            val = float(raw)
            min_val, max_val = VAR_BOUNDS[col_id]
            if val < min_val:
                adjusted_str = f"{min_val:.3f}".rstrip("0").rstrip(".")
                self.entries[col_id].delete(0, tk.END)
                self.entries[col_id].insert(0, adjusted_str)
                self.status_rule_lbl.config(
                    text=f"Aviso: Se ajustó al valor mínimo permitido ({min_val:.3f}) para '{col_id}'.",
                    foreground="#D97706",
                )
            elif val > max_val:
                adjusted_str = f"{max_val:.3f}".rstrip("0").rstrip(".")
                self.entries[col_id].delete(0, tk.END)
                self.entries[col_id].insert(0, adjusted_str)
            else:
                clean_str = f"{val:.3f}".rstrip("0").rstrip(".")
                self.entries[col_id].delete(0, tk.END)
                self.entries[col_id].insert(0, clean_str)

            self.calculate_prediction()
        except ValueError:
            pass

    def _on_combo_selected(self, col_id: str):
        """Maneja la selección de una etiqueta lingüística y asigna su valor representativo."""
        if self._updating_from_entry:
            return
        self._updating_from_combo = True
        idx = self.combos[col_id].current()
        if idx >= 0:
            _, repr_val, _ = LINGUISTIC_LABELS[col_id][idx]
            val_str = f"{repr_val:.3f}".rstrip("0").rstrip(".")
            self.entries[col_id].delete(0, tk.END)
            self.entries[col_id].insert(0, val_str)
            self.calculate_prediction()
        self._updating_from_combo = False

    def _on_entry_changed(self, col_id: str):
        """Sincroniza el combo lingüístico cuando se modifica el valor numérico."""
        if self._updating_from_combo:
            return
        self._updating_from_entry = True
        try:
            raw = self.entries[col_id].get().strip().replace(",", ".")
            if raw and raw != ".":
                val = float(raw)
                part_dict = self.fis.fuzzy_partitions.get(col_id, {})
                best_label = None
                best_mu = -1.0
                for lbl, (fn_type, params) in part_dict.items():
                    mu = float(trapmf(np.array([val]), params)[0]) if fn_type == "trap" else float(trimf(np.array([val]), params)[0])
                    if mu > best_mu:
                        best_mu = mu
                        best_label = lbl

                if best_label is not None and col_id in self.combos:
                    for i, (_, _, tag) in enumerate(LINGUISTIC_LABELS[col_id]):
                        if tag == best_label:
                            self.combos[col_id].current(i)
                            break
        except Exception:
            pass
        self._updating_from_entry = False

    def _sync_all_combos_from_entries(self):
        """Actualiza todos los combos de etiquetas para reflejar los valores numéricos actuales."""
        for col_id, _, _, _, _, _ in INPUT_SPECS:
            self._on_entry_changed(col_id)

    def load_preset(self, preset_key: str):
        """Carga los valores de un caso predefinido formateados a máximo 3 decimales."""
        if preset_key not in PRESETS:
            return
        vals = PRESETS[preset_key]["values"]
        for col_id, val in vals.items():
            if col_id in self.entries:
                val_str = f"{float(val):.3f}".rstrip("0").rstrip(".")
                self.entries[col_id].delete(0, tk.END)
                self.entries[col_id].insert(0, val_str)
        self._sync_all_combos_from_entries()
        self.calculate_prediction()

    def clear_fields(self):
        """Restaura todos los campos de entrada a sus valores por defecto válidos."""
        for col_id, _, _, def_val, _, _ in INPUT_SPECS:
            val_str = f"{def_val:.3f}".rstrip("0").rstrip(".")
            self.entries[col_id].delete(0, tk.END)
            self.entries[col_id].insert(0, val_str)
        self._sync_all_combos_from_entries()
        self.calculate_prediction()

    def _get_input_values(self) -> dict[str, float] | None:
        """Lee y valida estrictamente los valores ingresados en la interfaz."""
        values = {}
        for col_id, label_es, unit, _, min_val, max_val in INPUT_SPECS:
            raw = self.entries[col_id].get().strip().replace(",", ".")
            if not raw or raw == ".":
                messagebox.showerror(
                    "Dato Requerido",
                    f"El campo '{label_es}' no puede estar vacío.\n"
                    f"Debe ingresar un valor entre {min_val:.3f} y {max_val:.3f} {unit}."
                )
                self.entries[col_id].focus_set()
                return None
            try:
                val = float(raw)
            except ValueError:
                messagebox.showerror(
                    "Error Numérico",
                    f"'{raw}' no es un número válido para '{label_es}'."
                )
                self.entries[col_id].focus_set()
                return None

            if val < min_val or val > max_val:
                messagebox.showerror(
                    "Valor Fuera de Rango",
                    f"El valor de '{label_es}' debe estar dentro del rango permitido:\n\n"
                    f"[{min_val:.3f} - {max_val:.3f}] {unit}\n\n"
                    f"Valor ingresado: {val:.3f} {unit}."
                )
                self.entries[col_id].focus_set()
                return None

            values[col_id] = round(val, 3)
        return values

    def calculate_prediction(self):
        """Ejecuta la inferencia difusa sobre los valores ingresados y actualiza la UI."""
        data = self._get_input_values()
        if data is None:
            return

        df_input = pd.DataFrame([data])

        # 1. Inferencia continua
        pred_y, details = self.fis.predict(df_input, return_details=True)
        pred_val = float(pred_y[0])
        sum_w = float(details["sum_weights"][0])
        W = details["activation_matrix"][0]

        # 2. Relación agua / material cementante (a / mc)
        total_cementitious = data["cement"] + data["blast_furnace_slag"] + data["fly_ash"]
        if total_cementitious > 0:
            wc_ratio = data["water"] / total_cementitious
            wc_str = f"a/mc: {wc_ratio:.2f}"
        else:
            wc_str = "a/mc: N/A"
        self.wc_ratio_lbl.config(text=f"Relación {wc_str}")

        # 3. Categoría normativa ACI 318 / EN 206
        if pred_val < 20.0:
            cat_name = "Baja Resistencia (< 20 MPa)"
            cat_bg = "#FEF3C7"  # Amarillo claro
            cat_fg = "#92400E"
        elif pred_val < 35.0:
            cat_name = "Media-Baja (20 - 35 MPa)"
            cat_bg = "#DBEAFE"  # Azul claro
            cat_fg = "#1E40AF"
        elif pred_val <= 50.0:
            cat_name = "Media-Alta (35 - 50 MPa)"
            cat_bg = "#D1FAE5"  # Verde claro
            cat_fg = "#065F46"
        else:
            cat_name = "Alta Resistencia (> 50 MPa)"
            cat_bg = "#DCFCE7"  # Verde esmeralda
            cat_fg = "#14532D"

        self.res_val_lbl.config(text=f"{pred_val:.2f} MPa", foreground="#0F172A")
        self.class_badge.config(text=f"Clase: {cat_name}", bg=cat_bg, fg=cat_fg)

        # 4. Actualizar tabla de reglas disparadas
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)

        active_indices = np.where(W > 1e-4)[0]
        sorted_indices = active_indices[np.argsort(-W[active_indices])]

        n_active = len(sorted_indices)
        if n_active > 0:
            self.status_rule_lbl.config(
                text=f"Inferencia Activa: {n_active} de 15 reglas disparadas (Suma de pesos Σw = {sum_w:.3f}).",
                foreground="#047857",
            )
            for idx in sorted_indices:
                w_val = W[idx]
                cons, terms = self.fis.rules[idx]
                y_cent = self.fis.class_centroids[cons]
                logic_str = "IF " + " AND ".join([f"{a}=={l}" for a, l in terms]) + f" THEN {cons}"

                self.tree_rules.insert(
                    "",
                    tk.END,
                    values=(
                        f"R{idx+1}",
                        f"{w_val:.3f}",
                        cons.replace("_", " ").title(),
                        f"{y_cent:.2f}",
                        logic_str,
                    ),
                )
        else:
            self.status_rule_lbl.config(
                text=f"Fila Huérfana: Ninguna regla se activó (Σw = 0). Se aplicó escape por defecto ({self.fis.default_y:.2f} MPa).",
                foreground="#B91C1C",
            )

        # 5. Pertenencias difusas detalladas (calculadas sobre todas las particiones del sistema)
        self._update_memberships_view(df_input)

    def _update_memberships_view(self, df_input: pd.DataFrame):
        """Calcula y muestra los grados de pertenencia para TODAS las variables y etiquetas."""
        self.txt_membership.config(state=tk.NORMAL)
        self.txt_membership.delete("1.0", tk.END)

        text_lines = [
            "==================================================================",
            " GRADOS DE PERTENENCIA DIFUSA (μ) POR VARIABLE Y ETIQUETA",
            "==================================================================",
        ]

        # Iterar sobre TODAS las variables y etiquetas definidas en el sistema
        for col_id, label_es, unit, _, _, _ in INPUT_SPECS:
            val = float(df_input[col_id].iloc[0])
            part_dict = self.fis.fuzzy_partitions.get(col_id, {})
            text_lines.append(f"\n▶ [{label_es.upper()}] : {val:.3f} {unit}")

            for lbl, (fn_type, params) in part_dict.items():
                if fn_type == "trap":
                    mu_val = float(trapmf(np.array([val]), params)[0])
                elif fn_type == "tri":
                    mu_val = float(trimf(np.array([val]), params)[0])
                else:
                    mu_val = 0.0

                bar_len = int(round(mu_val * 20))
                bar = "█" * bar_len + "░" * (20 - bar_len)
                lbl_display = lbl.replace("_", " ").title().ljust(15)
                text_lines.append(f"   {lbl_display}: {mu_val:.3f} |{bar}|")

        self.txt_membership.insert(tk.END, "\n".join(text_lines))
        self.txt_membership.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = ConcreteFuzzyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
