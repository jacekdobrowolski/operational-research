import tkinter as tk
from tkinter import filedialog, messagebox
from amplpy import AMPL


def run_basic_model():
    try:
        ampl = AMPL()

        ampl.read("basic_model.mod")

        data_path = data_file_var.get()
        if not data_path:
            messagebox.showerror("Błąd", "Wybierz plik z danymi.")
            return

        ampl.read_data(data_path)
        ampl.setOption("solver", "gurobi")

        ampl.solve()

        results_text.delete(1.0, tk.END)

        results_text.insert(tk.END, "===== Wyniki: =====\n\n")

        results_text.insert(tk.END, "Wybrane Projekty:\n")
        var_x = ampl.get_variable('x')
        selected_projects = [
            index for index, value in var_x.get_values().to_dict().items() if value > 0.5
        ]
        for project in selected_projects:
            results_text.insert(tk.END, f" - Projekt: {project}\n")

        if not selected_projects:
            results_text.insert(tk.END, "  Nie wybrano żadnych projektów.\n")

        results_text.insert(tk.END, "\n")

        results_text.insert(tk.END, "Przypisanie Pracowników:\n")
        var_y = ampl.get_variable('y')
        assignments = [
            (i, p, j) for (i, p, j), value in var_y.get_values().to_dict().items() if value > 0.5
        ]
        for i, p, j in assignments:
            results_text.insert(tk.END, f" - Pracownik: {i} przypisany do Stanowiska: {p} w Projekcie: {j}\n")

        if not assignments:
            results_text.insert(tk.END, "  Nie przypisano żadnych pracowników do projektów.\n")

        results_text.insert(tk.END, "\nPodsumowanie:\n")
        results_text.insert(
            tk.END,
            "Na podstawie wyników modelu, wybrano projekty i przypisania pracowników, które zostały wyświetlone powyżej.\n"
        )

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas uruchamiania Modelu Podstawowego:\n{str(e)}")


def run_detailed_model():
    try:
        ampl = AMPL()

        ampl.read("detailed_model.mod")

        data_path = data_file_var.get()
        if not data_path:
            messagebox.showerror("Błąd", "Wybierz plik z danymi.")
            return

        ampl.read_data(data_path)

        ampl.setOption("solver", "gurobi")

        ampl.solve()

        results_text.delete(1.0, tk.END)

        results_text.insert(tk.END, "===== Wyniki: Model Szczegółowy =====\n\n")

        # Fetch the value of Cmax (objective function)
        Cmax = ampl.get_objective('ObjectiveFunction').value()
        results_text.insert(tk.END, f"Czas trwania projektu (Cmax): {Cmax}\n\n")

        # Get x{I, T} - Task schedule
        results_text.insert(tk.END, f"Harmonogram zadań (do czasu Cmax = {Cmax}):\n")
        var_x = ampl.get_variable('x')
        tasks_schedule = [
            (i, t) for (i, t), value in var_x.get_values().to_dict().items() if value > 0.5 and t <= Cmax
        ]
        for i, t in tasks_schedule:
            results_text.insert(tk.END, f" - Zadanie: {i} jest aktywne w czasie: {t}\n")

        if not tasks_schedule:
            results_text.insert(tk.END, "  Żadne zadanie nie jest aktywne.\n")

        results_text.insert(tk.END, "\n")

        # Display resource usage and availability until Cmax
        results_text.insert(tk.END, "Dostępność zasobów w czasie (do czasu Cmax):\n")
        D = ampl.get_parameter('D').get_values().to_dict()  # Dostępne zasoby
        requirement = ampl.get_parameter('d').get_values().to_dict()  # Wymagania zadań dla zasobów

        resource_usage = {}  # Klucz: (zasób R, czas T), wartość: suma przypisania
        free_resources = {}  # Klucz: (zasób R, czas T), wartość: ilość zasobu wolna

        for r in D.keys():
            for t in range(1, int(Cmax) + 1):  # Iteracja po czasie do Cmax
                # Oblicz przypisanie zasobu r w czasie t
                usage = sum(
                    requirement[i, r]  # Wymaganie zasobu r dla zadania i
                    for (i, t_prime), value in var_x.get_values().to_dict().items()
                    if t_prime == t and value > 0.5 and (i, r) in requirement
                )
                resource_usage[(r, t)] = usage
                free_resources[(r, t)] = D[r] - usage

        for t in range(1, int(Cmax) + 1):  # Ogranicz do czasu <= Cmax
            results_text.insert(tk.END, f"Etap nr {t}:\n")
            for r in D.keys():
                results_text.insert(tk.END, f" - Zasób: {r}, Przypisano: {resource_usage[(r, t)]}, Wolny: {free_resources[(r, t)]}\n")

        results_text.insert(tk.END, "\nPodsumowanie:\n")
        results_text.insert(
            tk.END,
            f"Projekt zakończy się w czasie  = {Cmax} tygodni.\n"
        )
        results_text.insert(tk.END, "Harmonogram zadań i dostępność zasobów wyświetlone powyżej.\n")

    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił błąd podczas uruchamiania Modelu Szczegółowego:\n{str(e)}")




def select_data_file():
    file_path = filedialog.askopenfilename(filetypes=[("AMPL Data Files", "*.dat")])
    data_file_var.set(file_path)


root = tk.Tk()
root.title("AMPL Model Runner")

tk.Label(root, text="Wybierz plik z danymi (.dat):").grid(row=0, column=0, sticky="w", padx=10, pady=5)
data_file_var = tk.StringVar()
tk.Entry(root, textvariable=data_file_var, width=50).grid(row=0, column=1, padx=10, pady=5)
tk.Button(root, text="Wybierz...", command=select_data_file).grid(row=0, column=2, padx=10, pady=5)

# Buttons to run the models
tk.Button(root, text="Wybierz projekty", command=run_basic_model, width=15).grid(row=1, column=0, padx=10, pady=10)
tk.Button(root, text="Zaplanuj projekt", command=run_detailed_model, width=15).grid(row=1, column=1, padx=10, pady=10)

# Results display
tk.Label(root, text="Wyniki:").grid(row=2, column=0, sticky="nw", padx=10, pady=5)
results_text = tk.Text(root, width=80, height=20)
results_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5)

# Start the Tkinter event loop
root.mainloop()
