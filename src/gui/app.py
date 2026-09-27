"""
Interfaz Gráfica de Escritorio (Desktop GUI) en Tkinter para el Sistema Difuso-Genético.
Permite evaluar mezclas personalizadas de concreto, cargar casos típicos predefinidos
y visualizar la estimación de resistencia (MPa) junto con la explicabilidad
de las reglas difusas activadas.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np

from src.fuzzy.inference import FuzzyInferenceSystem


# Especificación de variables de entrada con valores por defecto y rangos del dataset
INPUT_SPECS = [
    ("cement", "Cemento", "kg/m³", 330.0, "102 - 540"),
    ("blast_furnace_slag", "Escoria de Alto Horno", "kg/m³", 0.0, "0 - 360"),
    ("fly_ash", "Ceniza Volante", "kg/m³", 0.0, "0 - 200"),
    ("water", "Agua", "kg/m³", 180.0, "120 - 247"),
    ("superplasticizer", "Superplastificante", "kg/m³", 0.0, "0 - 32"),
    ("coarse_aggregate", "Agregado Grueso", "kg/m³", 1040.0, "800 - 1145"),
    ("fine_aggregate", "Agregado Fino", "kg/m³", 780.0, "594 - 992"),
    ("age", "Edad de Curado", "días", 28.0, "1 - 365"),
]

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
        self.root.geometry("1020x720")
        self.root.minsize(920, 640)

        # Cargar el motor sintonizado del AG
        try:
            self.fis = FuzzyInferenceSystem.from_tuned()
            self.model_status = "Modelo Sintonizado con AG (Activo)"
        except Exception as e:
            # Fallback al FIS nominal si no encuentra el archivo JSON
            self.fis = FuzzyInferenceSystem()
            self.model_status = f"Modelo Nominal Inicial (Línea Base: {e})"

        self._configure_styles()
        self._build_ui()
        self.load_preset("estandar")

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Configuración de estilos visuales limpios
        style.configure("Header.TLabel", font=("DejaVu Sans", 15, "bold"), foreground="#0F172A")
        style.configure("SubHeader.TLabel", font=("DejaVu Sans", 9), foreground="#64748B")
        style.configure("Section.TLabelframe.Label", font=("DejaVu Sans", 10, "bold"), foreground="#1E3A8A")
        style.configure("Primary.TButton", font=("DejaVu Sans", 11, "bold"), padding=6)
        style.configure("Preset.TButton", font=("DejaVu Sans", 9), padding=4)
        style.configure("Treeview.Heading", font=("DejaVu Sans", 9, "bold"))
        style.configure("Treeview", font=("DejaVu Sans", 9), rowheight=24)

    def _build_ui(self):
        # 1. Marco superior de encabezado
        header_frame = ttk.Frame(self.root, padding="15 10 15 5")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text="Predicción Inteligente de Resistencia a Compresión del Concreto",
            style="Header.TLabel",
        )
        title_lbl.pack(anchor=tk.W)

        sub_lbl = ttk.Label(
            header_frame,
            text=f"Motor de Inferencia Difuso con Reglas PRISM y Sintonización Genética | {self.model_status}",
            style="SubHeader.TLabel",
        )
        sub_lbl.pack(anchor=tk.W, pady=(2, 0))

        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=15, pady=8)

        # 2. Contenedor principal de dos columnas
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        left_container = ttk.Frame(main_paned, width=440)
        right_container = ttk.Frame(main_paned, width=540)
        main_paned.add(left_container, weight=4)
        main_paned.add(right_container, weight=6)

        # ====================================================================
        # COLUMNA IZQUIERDA: ENTRADAS Y CASOS PREDEFINIDOS
        # ====================================================================
        inputs_group = ttk.LabelFrame(left_container, text=" Dosificación de la Mezcla ", padding=10)
        inputs_group.pack(fill=tk.X, padx=5, pady=5)

        self.entries = {}
        for row_idx, (col_id, label_es, unit, def_val, range_hint) in enumerate(INPUT_SPECS):
            lbl = ttk.Label(inputs_group, text=f"{label_es}:", font=("DejaVu Sans", 9))
            lbl.grid(row=row_idx, column=0, sticky=tk.W, pady=3)

            entry = ttk.Entry(inputs_group, width=10, font=("DejaVu Sans", 9, "bold"), justify=tk.RIGHT)
            entry.insert(0, str(def_val))
            entry.grid(row=row_idx, column=1, sticky=tk.E, padx=(5, 5), pady=3)
            self.entries[col_id] = entry

            unit_lbl = ttk.Label(inputs_group, text=f"{unit} ({range_hint})", font=("DejaVu Sans", 8), foreground="#64748B")
            unit_lbl.grid(row=row_idx, column=2, sticky=tk.W, pady=3)

        # Marco de casos rápidos predefinidos
        preset_group = ttk.LabelFrame(left_container, text=" Casos Típicos de Ensayo (1-Click) ", padding=8)
        preset_group.pack(fill=tk.X, padx=5, pady=8)

        for key, pinfo in PRESETS.items():
            btn = ttk.Button(
                preset_group,
                text=pinfo["title"],
                style="Preset.TButton",
                command=lambda k=key: self.load_preset(k),
            )
            btn.pack(fill=tk.X, pady=2)

        # Botones de Acción
        actions_frame = ttk.Frame(left_container, padding="5 10 5 5")
        actions_frame.pack(fill=tk.X)

        calc_btn = ttk.Button(
            actions_frame,
            text="► CALCULAR RESISTENCIA (MPa)",
            style="Primary.TButton",
            command=self.calculate_prediction,
        )
        calc_btn.pack(fill=tk.X, ipady=4)

        reset_btn = ttk.Button(actions_frame, text="Limpiar Valores", command=self.clear_fields)
        reset_btn.pack(fill=tk.X, pady=(5, 0))

        # ====================================================================
        # COLUMNA DERECHA: RESULTADOS Y EXPLICABILIDAD DIFUSA
        # ====================================================================
        # Tarjeta principal de resultado
        result_group = ttk.LabelFrame(right_container, text=" Resistencia Estimada a Compresión ", padding=12)
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
        self.res_val_lbl.pack(fill=tk.X, pady=4)

        details_meta_frame = ttk.Frame(result_group)
        details_meta_frame.pack(fill=tk.X, pady=(6, 0))

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
        self.status_rule_lbl.pack(anchor=tk.W, pady=(8, 0))

        # Pestañas de Razonamiento y Reglas
        notebook = ttk.Notebook(right_container)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=8)

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
        self.tree_rules.column("logic", width=200, anchor=tk.W)

        scroll_y = ttk.Scrollbar(tab_rules, orient=tk.VERTICAL, command=self.tree_rules.yview)
        self.tree_rules.configure(yscrollcommand=scroll_y.set)
        self.tree_rules.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        # Pestaña 2: Pertenencias difusas
        tab_membership = ttk.Frame(notebook, padding=6)
        notebook.add(tab_membership, text=" Pertenencias Difusas (μ) ")

        self.txt_membership = tk.Text(tab_membership, wrap=tk.WORD, font=("Courier", 9), height=8, bg="#F8FAFC")
        scroll_m = ttk.Scrollbar(tab_membership, orient=tk.VERTICAL, command=self.txt_membership.yview)
        self.txt_membership.configure(yscrollcommand=scroll_m.set)
        self.txt_membership.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_m.pack(side=tk.RIGHT, fill=tk.Y)

    def load_preset(self, preset_key: str):
        """Carga los valores de un caso predefinido."""
        if preset_key not in PRESETS:
            return
        vals = PRESETS[preset_key]["values"]
        for col_id, val in vals.items():
            if col_id in self.entries:
                self.entries[col_id].delete(0, tk.END)
                self.entries[col_id].insert(0, str(val))
        self.calculate_prediction()

    def clear_fields(self):
        """Limpia todos los campos de entrada."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
            entry.insert(0, "0.0")
        self.res_val_lbl.config(text="--.-- MPa", foreground="#64748B")
        self.class_badge.config(text="Clase: Sin Calcular", bg="#E2E8F0", fg="#1E293B")
        self.wc_ratio_lbl.config(text="Relación a/mc: --")
        self.status_rule_lbl.config(text="Valores reiniciados.")
        for item in self.tree_rules.get_children():
            self.tree_rules.delete(item)
        self.txt_membership.delete("1.0", tk.END)

    def _get_input_values(self) -> dict[str, float] | None:
        """Lee y valida los valores ingresados en la interfaz."""
        values = {}
        for col_id, label_es, _, _, _ in INPUT_SPECS:
            raw = self.entries[col_id].get().strip().replace(",", ".")
            if not raw:
                messagebox.showerror("Dato Requerido", f"El campo '{label_es}' no puede estar vacío.")
                return None
            try:
                val = float(raw)
                if val < 0:
                    messagebox.showerror("Valor Inválido", f"El valor de '{label_es}' no puede ser negativo.")
                    return None
                values[col_id] = val
            except ValueError:
                messagebox.showerror("Error Numérico", f"'{raw}' no es un número válido para '{label_es}'.")
                return None
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
        # Ordenar de mayor a menor peso de activación
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

        # 5. Pertenencias difusas detalladas
        self._update_memberships_view(df_input)

    def _update_memberships_view(self, df_input: pd.DataFrame):
        """Calcula y muestra los grados de pertenencia para las variables de entrada."""
        self.txt_membership.delete("1.0", tk.END)

        memberships = self.fis.fuzzify_inputs(df_input)
        text_lines = ["--- GRADOS DE PERTENENCIA DIFUSA (μ) POR VARIABLE Y ETIQUETA ---"]

        # Agrupar por variable
        var_groups = {}
        for (var, label), mu in memberships.items():
            if var not in var_groups:
                var_groups[var] = []
            var_groups[var].append((label, float(mu[0])))

        for var, lbl_list in var_groups.items():
            text_lines.append(f"\n[{var.upper()}]:")
            for lbl, mu_val in lbl_list:
                bar_len = int(mu_val * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                text_lines.append(f"  {lbl.replace('_', ' ').ljust(14)}: {mu_val:.3f} |{bar}|")

        self.txt_membership.insert(tk.END, "\n".join(text_lines))


def main():
    root = tk.Tk()
    app = ConcreteFuzzyGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
