import tkinter as tk
from tkinter import messagebox, simpledialog
import qrcode
import speech_recognition as sr
from queue import Queue
import json

# Sample contact structure using a queue
contacts = Queue()

# File to store contacts data
CONTACTS_FILE = "contacts.json"

# Main Application Class
class PhonebookApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Connect Application")
        self.root.geometry("500x600")
        self.root.config(bg="lightblue")

        # Load contacts from file when the application starts
        self.load_contacts()

        # Adding main title
        title = tk.Label(root, text="Smart Connect", font=("Comic Sans Ms Bold", 20), bg="lightblue")
        title.pack(pady=10)

        # Search bar with suggestions
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.show_suggestions)
        search_entry = tk.Entry(root, textvariable=self.search_var, width=30, font=("Comic Sans Ms", 12))
        search_entry.pack(pady=5)

        # Voice search button
        voice_search_button = tk.Button(root, text="Voice Search", command=self.voice_search, width=20)
        voice_search_button.pack(pady=5)

        self.suggestions_frame = tk.Frame(root, bg="lightblue")
        self.suggestions_frame.pack(pady=5)

        # Adding Buttons
        btn_add = tk.Button(root, text="Add Contact", command=self.add_contact, width=20)
        btn_add.pack(pady=5)

        btn_view = tk.Button(root, text="View All Contacts", command=self.view_contacts, width=20)
        btn_view.pack(pady=5)

        btn_favorites = tk.Button(root, text="View Favorites", command=self.view_favorites, width=20)
        btn_favorites.pack(pady=5)

    def load_contacts(self):
        # Load contacts from the JSON file (if it exists)
        try:
            with open(CONTACTS_FILE, "r") as f:
                data = json.load(f)
                for contact in data:
                    contacts.put(contact)
        except FileNotFoundError:
            # If file doesn't exist, just start with an empty queue
            pass

    def save_contacts(self):
        # Save all contacts to a JSON file
        temp_contacts = []
        while not contacts.empty():
            contact = contacts.get()
            temp_contacts.append(contact)
            contacts.put(contact)  # Reinsert the contact back into the queue

        with open(CONTACTS_FILE, "w") as f:
            json.dump(temp_contacts, f)

    def add_contact(self):
        name = simpledialog.askstring("Add Contact", "Enter Contact Name:")
        phone = simpledialog.askstring("Add Contact", "Enter Contact Phone:")
        
        if name and phone:
            contact = {"name": name, "phone": phone, "favorite": False, "pinned": False}
            contacts.put(contact)  # Add contact to the queue
            self.save_contacts()  # Save contacts to file after adding
            messagebox.showinfo("Success", f"Contact '{name}' added successfully!")
        else:
            messagebox.showwarning("Input Error", "Please provide both name and phone.")

    def show_suggestions(self, *args):
        search_text = self.search_var.get().lower()
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        # Filter and show matching contacts
        temp_queue = Queue()
        while not contacts.empty():
            contact = contacts.get()
            if search_text in contact["name"].lower() or search_text in contact["phone"]:
                suggestion_text = f"{contact['name']} - {contact['phone']}"
                if contact['favorite']:
                    suggestion_text += " ★"
                suggestion_label = tk.Label(self.suggestions_frame, text=suggestion_text, font=("Comic Sans Ms", 12), bg="lightblue", cursor="hand2")
                suggestion_label.pack(anchor="w")
                suggestion_label.bind("<Button-1>", lambda e, c=contact: self.show_contact_details(c))
            temp_queue.put(contact)  # Reinsert contact
        while not temp_queue.empty():
            contacts.put(temp_queue.get())

    def show_contact_details(self, contact):
        contact_window = tk.Toplevel(self.root)
        contact_window.title("Contact Details")
        contact_window.geometry("300x300")
        contact_window.config(bg="lightgreen")

        name_label = tk.Label(contact_window, text=f"Name: {contact['name']}", font=("Comic Sans Ms", 14), bg="lightgreen")
        name_label.pack(pady=5)

        phone_label = tk.Label(contact_window, text=f"Phone: {contact['phone']}", font=("Comic Sans Ms", 14), bg="lightgreen")
        phone_label.pack(pady=5)

        fav_button_text = "Unfavorite" if contact["favorite"] else "Add to Favorites"
        fav_button = tk.Button(contact_window, text=fav_button_text, command=lambda: self.toggle_favorite(contact, fav_button))
        fav_button.pack(pady=5)

        # QR Code Button
        qr_button = tk.Button(contact_window, text="Generate QR Code", command=lambda: self.generate_qr_code(contact))
        qr_button.pack(pady=5)

        # Edit and Delete Buttons
        edit_button = tk.Button(contact_window, text="Edit Contact", command=lambda: self.edit_contact(contact))
        edit_button.pack(pady=5)

        delete_button = tk.Button(contact_window, text="Delete Contact", command=lambda: self.delete_contact(contact, contact_window))
        delete_button.pack(pady=5)

    def generate_qr_code(self, contact):
        qr_data = f"Name: {contact['name']}\nPhone: {contact['phone']}"
        qr = qrcode.make(qr_data)
        qr.show()

    def edit_contact(self, contact):
        new_name = simpledialog.askstring("Edit Contact", "Enter New Name:", initialvalue=contact["name"])
        new_phone = simpledialog.askstring("Edit Contact", "Enter New Phone:", initialvalue=contact["phone"])
        
        if new_name and new_phone:
            contact["name"] = new_name
            contact["phone"] = new_phone
            self.save_contacts()  # Save contacts to file after editing
            messagebox.showinfo("Success", f"Contact '{contact['name']}' updated successfully!")

    def delete_contact(self, contact, window):
        temp_queue = Queue()
        while not contacts.empty():
            current_contact = contacts.get()
            if current_contact != contact:
                temp_queue.put(current_contact)
        while not temp_queue.empty():
            contacts.put(temp_queue.get())
        self.save_contacts()  # Save contacts to file after deletion
        window.destroy()
        messagebox.showinfo("Deleted", f"Contact '{contact['name']}' has been deleted.")

    def toggle_favorite(self, contact, button):
        contact["favorite"] = not contact["favorite"]
        button_text = "Unfavorite" if contact["favorite"] else "Add to Favorites"
        button.config(text=button_text)
        status = "added to" if contact["favorite"] else "removed from"
        self.save_contacts()  # Save contacts to file after favoriting/unfavoriting
        messagebox.showinfo("Favorite", f"Contact '{contact['name']}' {status} favorites.")

    def view_contacts(self):
        contact_list = tk.Toplevel(self.root)
        contact_list.title("All Contacts")
        contact_list.geometry("300x400")
        contact_list.config(bg="lightyellow")

        temp_queue = Queue()
        while not contacts.empty():
            contact = contacts.get()
            info = f"{contact['name']} - {contact['phone']} {'★' if contact['favorite'] else ''}"
            label = tk.Label(contact_list, text=info, font=("Comic Sans Ms", 12), bg="lightyellow", cursor="hand2")
            label.pack()
            label.bind("<Button-1>", lambda e, c=contact: self.show_contact_details(c))
            temp_queue.put(contact)
        while not temp_queue.empty():
            contacts.put(temp_queue.get())

    def view_favorites(self):
        favorite_list = tk.Toplevel(self.root)
        favorite_list.title("Favorites")
        favorite_list.geometry("300x400")
        favorite_list.config(bg="lightgreen")

        temp_queue = Queue()
        while not contacts.empty():
            contact = contacts.get()
            if contact["favorite"]:
                info = f"{contact['name']} - {contact['phone']} ★"
                label = tk.Label(favorite_list, text=info, font=("Comic Sans Ms", 12), bg="lightgreen")
                label.pack()
                label.bind("<Button-1>", lambda e, c=contact: self.show_contact_details(c))
            temp_queue.put(contact)
        while not temp_queue.empty():
            contacts.put(temp_queue.get())

    def voice_search(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            messagebox.showinfo("Voice Search", "Speak now to search for a contact.")
            try:
                audio = recognizer.listen(source, timeout=5)
                search_text = recognizer.recognize_google(audio).lower()
                self.search_var.set(search_text)
            except sr.UnknownValueError:
                messagebox.showerror("Error", "Could not understand audio.")
            except sr.RequestError:
                messagebox.showerror("Error", "Could not request results; check internet connection.")
            except sr.WaitTimeoutError:
                messagebox.showerror("Error", "Listening timed out.")

# Initialize Application
root = tk.Tk()
app = PhonebookApp(root)
root.mainloop()
