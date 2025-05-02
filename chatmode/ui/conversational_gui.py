import tkinter as tk
from tkinter import scrolledtext
from chatmode.conversational_core import ConversationalCore
import threading # To run LLM processing in a separate thread

class ConversationalGUI(tk.Tk):
    def __init__(self):
        """
        Initializes the Conversational GUI.
        """
        super().__init__()

        self.title("Pulse AI Conversational Interface")
        self.geometry("700x500")

        # Initialize the ConversationalCore
        self.conversational_core = ConversationalCore()

        # --- UI Elements ---
        # Conversation History Display
        self.history_display = scrolledtext.ScrolledText(self, wrap=tk.WORD, state='disabled', font=('Arial', 10))
        self.history_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Input Area (Frame to hold input field and send button)
        input_frame = tk.Frame(self)
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        # User Input Field
        self.user_input = tk.Entry(input_frame, font=('Arial', 10))
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind("<Return>", self.send_message_event) # Bind Enter key

        # Send Button
        self.send_button = tk.Button(input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # --- Initial Message ---
        self.display_message("Pulse AI: Hello! How can I help you with the Pulse codebase today?\n")

    def display_message(self, message):
        """
        Displays a message in the conversation history area.
        """
        self.history_display.config(state='normal')
        self.history_display.insert(tk.END, message)
        self.history_display.yview(tk.END) # Auto-scroll to the bottom
        self.history_display.config(state='disabled')

    def send_message_event(self, event):
        """
        Handles sending message when Enter key is pressed.
        """
        self.send_message()

    def send_message(self):
        """
        Sends the user's message to the conversational core and displays the response.
        """
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        self.display_message(f"User: {user_text}\n")
        self.user_input.delete(0, tk.END) # Clear input field
        self.send_button.config(state='disabled') # Disable send button while processing

        # Process the query in a separate thread to keep the GUI responsive
        threading.Thread(target=self._process_query_in_thread, args=(user_text,)).start()

    def _process_query_in_thread(self, user_text):
        """
        Processes the query using the conversational core in a separate thread.
        """
        try:
            response, retrieved_snippets = self.conversational_core.process_query(user_text)
            # Display the response in the main GUI thread
            self.after(0, self.display_message, f"Pulse AI: {response}\n")

            # Optionally display retrieved snippets
            if retrieved_snippets:
                 snippet_text = "\n\n".join([f"--- Snippet ---\n{s[:300]}..." for s in retrieved_snippets]) # Display first 300 chars
                 self.after(0, self.display_message, f"Retrieved Snippets:\n{snippet_text}\n")

        except Exception as e:
            self.after(0, self.display_message, f"Error processing query: {e}\n")
            print(f"Error processing query: {e}")
        finally:
            # Re-enable the send button in the main GUI thread
            self.after(0, self.send_button.config, state='normal')


if __name__ == '__main__':
    # To run this GUI, you need to have built the vector store first
    # by running chatmode/vector_store/build_vector_store.py

    app = ConversationalGUI()
    app.mainloop()