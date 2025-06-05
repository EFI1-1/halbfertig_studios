import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import random
import sqlite3
import os

DB_NAME = "vokabeln.db"


def init_db():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS vokabeln
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       englisch
                       TEXT
                       NOT
                       NULL
                       UNIQUE,
                       deutsch
                       TEXT
                       NOT
                       NULL
                   )
                   ''')
    conn.commit()
    conn.close()


def lade_vokabeln_aus_db(mit_id=False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if mit_id:
        cursor.execute("SELECT id, englisch, deutsch FROM vokabeln ORDER BY englisch")
        vokabeln_db = [dict(row) for row in cursor.fetchall()]
    else:
        cursor.execute("SELECT englisch, deutsch FROM vokabeln ORDER BY englisch")
        vokabeln_db = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return vokabeln_db


def speichere_vokabel_in_db(englisch, deutsch):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO vokabeln (englisch, deutsch) VALUES (?, ?)", (englisch, deutsch))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def aktualisiere_vokabel_in_db(vok_id, englisch, deutsch):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE vokabeln SET englisch = ?, deutsch = ? WHERE id = ?", (englisch, deutsch, vok_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        messagebox.showerror("Fehler",
                             f"Das englische Wort '{englisch}' existiert bereits oder ein anderer Fehler ist aufgetreten.")
        return False
    finally:
        conn.close()


def loesche_vokabel_aus_db(vok_id):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM vokabeln WHERE id = ?", (vok_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        messagebox.showerror("Fehler", f"Fehler beim Löschen der Vokabel: {e}")
        return False
    finally:
        conn.close()


class VokabelBearbeitenDialog(simpledialog.Dialog):
    def __init__(self, parent, title, vokabel_id, englisch_alt, deutsch_alt):
        self.vokabel_id = vokabel_id
        self.englisch_alt = englisch_alt
        self.deutsch_alt = deutsch_alt
        self.neue_daten = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Englisches Wort:").grid(row=0, sticky=tk.W)
        tk.Label(master, text="Deutsche Übersetzung:").grid(row=1, sticky=tk.W)

        self.entry_englisch = tk.Entry(master, width=30)
        self.entry_englisch.grid(row=0, column=1, padx=5, pady=5)
        self.entry_englisch.insert(0, self.englisch_alt)

        self.entry_deutsch = tk.Entry(master, width=30)
        self.entry_deutsch.grid(row=1, column=1, padx=5, pady=5)
        self.entry_deutsch.insert(0, self.deutsch_alt)
        return self.entry_englisch

    def apply(self):
        englisch_neu_raw = self.entry_englisch.get().strip()
        deutsch_neu_raw = self.entry_deutsch.get().strip()

        if not englisch_neu_raw or not deutsch_neu_raw:
            messagebox.showwarning("Ungültig", "Felder dürfen nicht leer sein.", parent=self)
            self.neue_daten = None
            return

        self.neue_daten = (self.vokabel_id, englisch_neu_raw.lower(), deutsch_neu_raw.lower())


class Vokabeltrainer:
    def __init__(self, master):
        self.master = master
        master.title("Vokabeltrainer mit DB")
        master.geometry("450x350")

        self.vokabeln = lade_vokabeln_aus_db()
        if not self.vokabeln:
            initial_vokabeln = [
                ("hello", "hallo"), ("world", "Welt"), ("cat", "Katze"),
                ("dog", "Hund"), ("house", "Haus")
            ]
            for eng, deu in initial_vokabeln:
                if speichere_vokabel_in_db(eng.lower(), deu.lower()):
                    self.vokabeln.append({"englisch": eng.lower(), "deutsch": deu.lower()})
            if not self.vokabeln:
                messagebox.showinfo("Info", "Keine Vokabeln. Bitte füge welche hinzu.", parent=self.master)

        self.aktuelle_vokabel = None
        self.score = 0
        self.versuche = 0
        # NEU: Flag, um Mehrfachprüfung zu verhindern
        self.antwort_geprueft_fuer_aktuelle_vokabel = True  # Standardmäßig True, da anfangs keine Vokabel aktiv ist

        self.label_info = tk.Label(master, text="Übersetze das englische Wort:", font=("Arial", 14))
        self.label_info.pack(pady=10)

        self.label_englisch = tk.Label(master, text="", font=("Arial", 18, "bold"))
        self.label_englisch.pack(pady=10)

        self.entry_deutsch = tk.Entry(master, font=("Arial", 14))
        self.entry_deutsch.pack(pady=10)
        self.entry_deutsch.bind("<Return>", self.pruefe_antwort_event)

        self.button_pruefen = tk.Button(master, text="Prüfen", command=self.pruefe_antwort, font=("Arial", 12))
        self.button_pruefen.pack(pady=5)

        self.label_feedback = tk.Label(master, text="", font=("Arial", 12))
        self.label_feedback.pack(pady=10)

        self.label_score = tk.Label(master, text=f"Score: {self.score}/{self.versuche}", font=("Arial", 12))
        self.label_score.pack(pady=5)

        self.button_naechste = tk.Button(master, text="Nächste Vokabel", command=self.naechste_vokabel,
                                         font=("Arial", 12))
        self.button_naechste.pack(pady=5)

        menubar = tk.Menu(master)
        optionsmenu = tk.Menu(menubar, tearoff=0)
        optionsmenu.add_command(label="Vokabel hinzufügen", command=self.vokabel_hinzufuegen)
        optionsmenu.add_command(label="Alle Vokabeln anzeigen/verwalten", command=self.zeige_alle_vokabeln)
        optionsmenu.add_separator()
        optionsmenu.add_command(label="Programm beenden", command=master.quit)
        menubar.add_cascade(label="Optionen", menu=optionsmenu)
        master.config(menu=menubar)

        self.naechste_vokabel()

    def _update_main_app_vokabeln_and_ui(self):
        self.vokabeln = lade_vokabeln_aus_db()
        current_english_word = self.aktuelle_vokabel["englisch"] if self.aktuelle_vokabel else None

        if not self.vokabeln:
            self.naechste_vokabel()
            return

        if current_english_word and not any(v["englisch"] == current_english_word for v in self.vokabeln):
            self.naechste_vokabel()

    def naechste_vokabel(self):
        if not self.vokabeln:
            self.label_englisch.config(text="Keine Vokabeln!")
            self.entry_deutsch.config(state=tk.DISABLED)
            self.button_pruefen.config(state=tk.DISABLED)
            self.button_naechste.config(state=tk.DISABLED)
            self.label_feedback.config(text="Bitte füge zuerst Vokabeln über das Menü hinzu.", fg="blue")
            self.aktuelle_vokabel = None
            self.antwort_geprueft_fuer_aktuelle_vokabel = True  # Keine Vokabel zum Prüfen
            return

        self.aktuelle_vokabel = random.choice(self.vokabeln)
        self.label_englisch.config(text=self.aktuelle_vokabel["englisch"])
        self.label_feedback.config(text="")
        self.entry_deutsch.config(state=tk.NORMAL)
        self.entry_deutsch.delete(0, tk.END)
        self.entry_deutsch.focus()
        self.button_pruefen.config(state=tk.NORMAL)
        # NEU: Flag zurücksetzen für die neue Vokabel
        self.antwort_geprueft_fuer_aktuelle_vokabel = False

    def pruefe_antwort_event(self, event):
        # Diese Hilfsfunktion ist nützlich, falls man später noch Event-spezifische Dinge tun wollte
        self.pruefe_antwort()

    def pruefe_antwort(self):
        # NEU: Prüfen, ob für diese Vokabel die Antwort schon gegeben wurde
        if not self.aktuelle_vokabel or self.antwort_geprueft_fuer_aktuelle_vokabel:
            return  # Nichts tun, wenn schon geprüft oder keine aktuelle Vokabel

        user_antwort_raw = self.entry_deutsch.get()
        user_antwort_stripped = user_antwort_raw.strip()
        korrekte_antwort = self.aktuelle_vokabel["deutsch"]

        self.versuche += 1

        if not user_antwort_stripped:
            self.label_feedback.config(text=f"Falsch. Keine Antwort. Richtig: {korrekte_antwort}", fg="red")
        elif user_antwort_stripped.lower() == korrekte_antwort:
            self.score += 1
            self.label_feedback.config(text="Richtig! :)", fg="green")
        else:
            self.label_feedback.config(text=f"Falsch. Richtig ist: {korrekte_antwort}", fg="red")

        self.label_score.config(text=f"Score: {self.score}/{self.versuche}")

        # NEU: Flag setzen, dass geprüft wurde
        self.antwort_geprueft_fuer_aktuelle_vokabel = True
        # Eingabefeld und Prüfbutton deaktivieren
        self.entry_deutsch.config(state=tk.DISABLED)
        self.button_pruefen.config(state=tk.DISABLED)

    def vokabel_hinzufuegen(self):
        englisch_neu_raw = simpledialog.askstring("Neue Vokabel", "Englisches Wort:", parent=self.master)
        if englisch_neu_raw is None: return

        englisch_neu_stripped = englisch_neu_raw.strip()
        if not englisch_neu_stripped:
            messagebox.showwarning("Ungültig", "Englisches Wort darf nicht leer sein.", parent=self.master)
            return

        deutsch_neu_raw = simpledialog.askstring("Neue Vokabel", f"Deutsche Übersetzung für '{englisch_neu_stripped}':",
                                                 parent=self.master)
        if deutsch_neu_raw is None: return

        deutsch_neu_stripped = deutsch_neu_raw.strip()
        if not deutsch_neu_stripped:
            messagebox.showwarning("Ungültig", "Deutsche Übersetzung darf nicht leer sein.", parent=self.master)
            return

        englisch_neu_lower = englisch_neu_stripped.lower()
        deutsch_neu_lower = deutsch_neu_stripped.lower()

        if speichere_vokabel_in_db(englisch_neu_lower, deutsch_neu_lower):
            messagebox.showinfo("Erfolg", f"Vokabel '{englisch_neu_lower} - {deutsch_neu_lower}' hinzugefügt.",
                                parent=self.master)
            self._update_main_app_vokabeln_and_ui()
            if len(self.vokabeln) == 1 and not self.antwort_geprueft_fuer_aktuelle_vokabel:  # Wenn es die erste Vokabel war und noch nicht angezeigt/geprüft
                self.naechste_vokabel()  # Um die UI zu aktualisieren und die erste Vokabel anzuzeigen
            elif self.button_naechste[
                'state'] == tk.DISABLED and self.vokabeln:  # Fall: vorher keine Vokabeln, jetzt schon
                self.naechste_vokabel()


        else:
            messagebox.showerror("Fehler", f"Das englische Wort '{englisch_neu_lower}' existiert bereits.",
                                 parent=self.master)

    def zeige_alle_vokabeln(self):
        top = tk.Toplevel(self.master)
        top.title("Alle Vokabeln Verwalten")
        top.geometry("600x450")

        frame = ttk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("id", "englisch", "deutsch")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("id", text="ID")
        tree.heading("englisch", text="Englisch")
        tree.heading("deutsch", text="Deutsch")
        tree.column("id", width=50, anchor=tk.CENTER, stretch=tk.NO)
        tree.column("englisch", width=200, anchor=tk.W)
        tree.column("deutsch", width=200, anchor=tk.W)

        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar_y.set)
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscroll=scrollbar_x.set)

        tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        def _populate_tree():
            for i in tree.get_children():
                tree.delete(i)
            alle_vokabeln_liste_dicts = lade_vokabeln_aus_db(mit_id=True)
            if not alle_vokabeln_liste_dicts:
                tree.insert("", tk.END, values=("", "Keine Vokabeln vorhanden", ""))
            else:
                for vok_dict in alle_vokabeln_liste_dicts:
                    tree.insert("", tk.END, values=(vok_dict["id"], vok_dict["englisch"], vok_dict["deutsch"]))

        _populate_tree()

        button_frame = ttk.Frame(top)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        def _get_selected_vokabel_data():
            selected_item_focus_id = tree.focus()
            if not selected_item_focus_id:
                messagebox.showwarning("Auswahl", "Bitte zuerst eine Vokabel auswählen.", parent=top)
                return None

            item_content = tree.item(selected_item_focus_id)
            values = item_content['values']

            if not values or not isinstance(values, (list, tuple)) or len(values) < 3 or not values[0]:
                messagebox.showwarning("Auswahl", "Keine gültige Vokabel ausgewählt.", parent=top)
                return None
            return {"id": values[0], "englisch": values[1], "deutsch": values[2]}

        def _vokabel_bearbeiten():
            selected_data = _get_selected_vokabel_data()
            if not selected_data: return

            dialog = VokabelBearbeitenDialog(top, "Vokabel bearbeiten",
                                             selected_data["id"],
                                             selected_data["englisch"],
                                             selected_data["deutsch"])
            if dialog.neue_daten:
                vok_id, eng_neu, deu_neu = dialog.neue_daten
                if aktualisiere_vokabel_in_db(vok_id, eng_neu, deu_neu):
                    messagebox.showinfo("Erfolg", "Vokabel erfolgreich aktualisiert.", parent=top)
                    _populate_tree()
                    self._update_main_app_vokabeln_and_ui()

        def _vokabel_loeschen():
            selected_data = _get_selected_vokabel_data()
            if not selected_data: return

            confirm = messagebox.askyesno("Löschen bestätigen",
                                          f"Möchten Sie die Vokabel '{selected_data['englisch']} - {selected_data['deutsch']}' wirklich löschen?",
                                          parent=top)
            if confirm:
                if loesche_vokabel_aus_db(selected_data["id"]):
                    messagebox.showinfo("Erfolg", "Vokabel gelöscht.", parent=top)
                    _populate_tree()
                    self._update_main_app_vokabeln_and_ui()

        edit_button = ttk.Button(button_frame, text="Bearbeiten", command=_vokabel_bearbeiten)
        edit_button.pack(side=tk.LEFT, padx=5)

        delete_button = ttk.Button(button_frame, text="Löschen", command=_vokabel_loeschen)
        delete_button.pack(side=tk.LEFT, padx=5)

        refresh_button = ttk.Button(button_frame, text="Aktualisieren", command=_populate_tree)
        refresh_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(top, text="Schließen", command=top.destroy)
        close_button.pack(pady=10)

        top.transient(self.master)
        top.grab_set()
        self.master.wait_window(top)


if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = Vokabeltrainer(root)
    root.mainloop()