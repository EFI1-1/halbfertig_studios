import tkinter as tk
from tkinter import simpledialog, messagebox, ttk # ttk für Treeview hinzugefügt
import random
import sqlite3
import os

# Name der Datenbankdatei
DB_NAME = "vokabeln.db"

def init_db():
    """Initialisiert die Datenbank und erstellt die Tabelle, falls sie nicht existiert."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vokabeln (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            englisch TEXT NOT NULL UNIQUE,
            deutsch TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def lade_vokabeln_aus_db(mit_id=False):
    """Lädt alle Vokabeln aus der Datenbank.
    Wenn mit_id=True, werden auch die IDs geladen.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, DB_NAME)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if mit_id:
        cursor.execute("SELECT id, englisch, deutsch FROM vokabeln ORDER BY englisch")
        vokabeln_db = cursor.fetchall()
        conn.close()
        return vokabeln_db # Gibt Tupel (id, englisch, deutsch) zurück
    else:
        cursor.execute("SELECT englisch, deutsch FROM vokabeln")
        vokabeln_db = cursor.fetchall()
        conn.close()
        # Umwandeln in das Format, das der Trainer erwartet (Liste von Dictionaries)
        return [{"englisch": eng, "deutsch": deu} for eng, deu in vokabeln_db]


def speichere_vokabel_in_db(englisch, deutsch):
    """Speichert eine neue Vokabel in der Datenbank."""
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

class Vokabeltrainer:
    def __init__(self, master):
        self.master = master
        master.title("Vokabeltrainer mit DB")
        master.geometry("450x350")

        self.vokabeln = lade_vokabeln_aus_db()
        if not self.vokabeln:
            initial_vokabeln = [
                ("hello", "hallo"), ("world", "Welt"), ("cat", "Katze"),
                ("dog", "Hund"), ("house", "Haus"), ("book", "Buch"),
                ("computer", "Computer"), ("school", "Schule"),
                ("teacher", "Lehrer"), ("student", "Schüler")
            ]
            for eng, deu in initial_vokabeln:
                if speichere_vokabel_in_db(eng, deu):
                    self.vokabeln.append({"englisch": eng, "deutsch": deu})
            if not self.vokabeln:
                 messagebox.showinfo("Info", "Keine Vokabeln in der Datenbank. Bitte füge welche hinzu.", parent=self.master)


        self.aktuelle_vokabel = None
        self.score = 0
        self.versuche = 0

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

        self.button_naechste = tk.Button(master, text="Nächste Vokabel", command=self.naechste_vokabel, font=("Arial", 12))
        self.button_naechste.pack(pady=5)

        menubar = tk.Menu(master)
        optionsmenu = tk.Menu(menubar, tearoff=0)
        optionsmenu.add_command(label="Vokabel hinzufügen", command=self.vokabel_hinzufuegen)
        optionsmenu.add_command(label="Alle Vokabeln anzeigen", command=self.zeige_alle_vokabeln) # Neuer Menüpunkt
        optionsmenu.add_separator()
        optionsmenu.add_command(label="Programm beenden", command=master.quit)
        menubar.add_cascade(label="Optionen", menu=optionsmenu)
        master.config(menu=menubar)

        self.naechste_vokabel()

    def naechste_vokabel(self):
        if not self.vokabeln:
            self.label_englisch.config(text="Keine Vokabeln!")
            self.entry_deutsch.config(state=tk.DISABLED)
            self.button_pruefen.config(state=tk.DISABLED)
            self.button_naechste.config(state=tk.DISABLED)
            self.label_feedback.config(text="Bitte füge zuerst Vokabeln über das Menü hinzu.", fg="blue")
            return

        self.aktuelle_vokabel = random.choice(self.vokabeln)
        self.label_englisch.config(text=self.aktuelle_vokabel["englisch"])
        self.label_feedback.config(text="")
        self.entry_deutsch.config(state=tk.NORMAL)
        self.entry_deutsch.delete(0, tk.END)
        self.entry_deutsch.focus()
        self.button_pruefen.config(state=tk.NORMAL)

    def pruefe_antwort_event(self, event):
        self.pruefe_antwort()

    def pruefe_antwort(self):
        if not self.aktuelle_vokabel:
            return

        user_antwort = self.entry_deutsch.get().strip().lower()
        korrekte_antwort = self.aktuelle_vokabel["deutsch"].lower()

        self.versuche += 1
        if user_antwort == korrekte_antwort:
            self.score += 1
            self.label_feedback.config(text="Richtig! :)", fg="green")
        else:
            self.label_feedback.config(text=f"Falsch. Richtig ist: {self.aktuelle_vokabel['deutsch']}", fg="red")

        self.label_score.config(text=f"Score: {self.score}/{self.versuche}")
        self.entry_deutsch.config(state=tk.DISABLED)
        self.button_pruefen.config(state=tk.DISABLED)

    def vokabel_hinzufuegen(self):
        englisch_neu = simpledialog.askstring("Neue Vokabel", "Englisches Wort:", parent=self.master)
        if englisch_neu:
            englisch_neu = englisch_neu.strip().lower()
            if not englisch_neu:
                 messagebox.showwarning("Ungültig", "Englisches Wort darf nicht leer sein.", parent=self.master)
                 return

            deutsch_neu = simpledialog.askstring("Neue Vokabel", f"Deutsche Übersetzung für '{englisch_neu}':", parent=self.master)
            if deutsch_neu:
                deutsch_neu = deutsch_neu.strip().lower()
                if not deutsch_neu:
                    messagebox.showwarning("Ungültig", "Deutsche Übersetzung darf nicht leer sein.", parent=self.master)
                    return

                if speichere_vokabel_in_db(englisch_neu, deutsch_neu):
                    self.vokabeln.append({"englisch": englisch_neu, "deutsch": deutsch_neu})
                    messagebox.showinfo("Erfolg", f"Vokabel '{englisch_neu} - {deutsch_neu}' hinzugefügt.", parent=self.master)
                    if len(self.vokabeln) == 1 and not self.aktuelle_vokabel:
                        self.naechste_vokabel()
                else:
                    messagebox.showerror("Fehler", f"Das englische Wort '{englisch_neu}' existiert bereits in der Datenbank.", parent=self.master)

    def zeige_alle_vokabeln(self):
        """Zeigt alle Vokabeln aus der Datenbank in einem neuen Fenster an."""
        alle_vokabeln_liste = lade_vokabeln_aus_db(mit_id=True) # Lade mit IDs

        if not alle_vokabeln_liste:
            messagebox.showinfo("Info", "Die Datenbank enthält keine Vokabeln.", parent=self.master)
            return

        # Neues Toplevel-Fenster erstellen
        top = tk.Toplevel(self.master)
        top.title("Alle Vokabeln")
        top.geometry("500x400") # Größe des Fensters anpassen

        # Frame für Treeview und Scrollbar
        frame = ttk.Frame(top)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Spalten definieren
        columns = ("id", "englisch", "deutsch")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Überschriften für die Spalten
        tree.heading("id", text="ID")
        tree.heading("englisch", text="Englisch")
        tree.heading("deutsch", text="Deutsch")

        # Spaltenbreiten anpassen
        tree.column("id", width=50, anchor=tk.CENTER)
        tree.column("englisch", width=200, anchor=tk.W) # W = West (linksbündig)
        tree.column("deutsch", width=200, anchor=tk.W)

        # Daten einfügen
        for vokabel_tuple in alle_vokabeln_liste:
            tree.insert("", tk.END, values=vokabel_tuple)

        # Scrollbar hinzufügen
        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar_y.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(xscroll=scrollbar_x.set)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        tree.pack(fill=tk.BOTH, expand=True)

        # Button zum Schließen des Fensters
        close_button = ttk.Button(top, text="Schließen", command=top.destroy)
        close_button.pack(pady=10)
        top.transient(self.master)
        top.grab_set()
        self.master.wait_window(top)


# Hauptprogramm
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = Vokabeltrainer(root)
    root.mainloop()