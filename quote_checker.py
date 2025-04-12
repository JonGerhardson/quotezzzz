# VERSION: 2025-04-12_1540 (Replaced right-click flag with buttons)

import tkinter as tk
from tkinter import ttk
# Removed Menu import
from tkinter import filedialog, scrolledtext, messagebox, Listbox, Frame as tkFrame, Label as tkLabel, Button as tkButton, Checkbutton as tkCheckbutton, PanedWindow as tkPanedWindow, Scrollbar, BooleanVar, TclError, font as tkFont, END, BOTH, LEFT, RIGHT, Y, TOP, BOTTOM, X, VERTICAL, SEL, INSERT, W

import re
import difflib
import os

# --- Configuration ---
HIGHLIGHT_COLOR_DOC = "#ADD8E6"; HIGHLIGHT_COLOR_TRANSCRIPT_GOOD = "#D4EDDA"; HIGHLIGHT_COLOR_TRANSCRIPT_LOW = "#FFF3CD"
LISTBOX_SELECT_BG = "#CCE5FF"; LISTBOX_SELECT_FG = "#004085"; LISTBOX_EVEN_ROW_BG = "white"; LISTBOX_ODD_ROW_BG = "#f0f0f0"
MATCH_THRESHOLD = 0.80
FLAG_INDICATOR = "* "

# --- Core Logic (find_quotes, find_best_match - unchanged) ---
def find_quotes(text):
    """Finds quotes ("...") and their positions within the Document."""
    quotes = []
    for match in re.finditer(r'"(.*?)"', text, re.DOTALL):
        quote_text = match.group(1).strip()
        if quote_text:
            quotes.append({
                "text": quote_text,
                "start": match.start(),
                "end": match.end(),
                "flagged": False  # <<< THIS LINE WAS MISSING - Ensure flag initialized
                })
    return quotes
    
def find_best_match(quote_text, transcript_text):
    best_match = None; highest_ratio = 0.0; s = difflib.SequenceMatcher(None, quote_text, transcript_text, autojunk=False)
    match_info = s.find_longest_match(0, len(quote_text), 0, len(transcript_text))
    if match_info.size > 0:
        potential_match_start = max(0, match_info.b - len(quote_text) // 4); potential_match_end = min(len(transcript_text), match_info.b + match_info.size + len(quote_text) // 4)
        transcript_segment = transcript_text[potential_match_start:potential_match_end]; s_segment = difflib.SequenceMatcher(None, quote_text, transcript_segment, autojunk=False)
        segment_match_info = s_segment.find_longest_match(0, len(quote_text), 0, len(transcript_segment))
        if segment_match_info.size > 0:
            transcript_match_segment = transcript_segment[segment_match_info.b : segment_match_info.b + len(quote_text)]; final_ratio = difflib.SequenceMatcher(None, quote_text, transcript_match_segment).ratio()
            transcript_start_index = potential_match_start + segment_match_info.b; transcript_end_index = transcript_start_index + len(transcript_match_segment)
            if final_ratio > highest_ratio:
                highest_ratio = final_ratio; best_match = {"transcript_start": transcript_start_index, "transcript_end": transcript_end_index, "ratio": final_ratio, "matched_text": transcript_text[transcript_start_index:transcript_end_index]}
    if (not best_match or best_match["ratio"] < MATCH_THRESHOLD) and match_info.size > 0:
        initial_match_segment = transcript_text[match_info.b : match_info.b + len(quote_text)]; initial_ratio = difflib.SequenceMatcher(None, quote_text, initial_match_segment).ratio()
        if initial_ratio > highest_ratio and initial_ratio >= MATCH_THRESHOLD * 0.9:
            highest_ratio = initial_ratio; best_match = {"transcript_start": match_info.b, "transcript_end": match_info.b + len(initial_match_segment), "ratio": initial_ratio, "matched_text": initial_match_segment}
    return best_match

# --- GUI Class ---
class QuoteCheckerApp:

    def __init__(self, master):
        self.master = master
        master.title("Quote Verifier")
        master.geometry("1250x800")

        # Fonts
        self.text_font = tkFont.Font(family="Segoe UI", size=11); self.label_font = tkFont.Font(family="Segoe UI", size=11, weight="bold"); self.list_font = tkFont.Font(family="Segoe UI", size=11); self.button_font = tkFont.Font(family="Segoe UI", size=10); self.status_font = tkFont.Font(family="Segoe UI", size=10); self.info_label_font = tkFont.Font(family="Segoe UI", size=10, weight="bold"); self.info_value_font = tkFont.Font(family="Segoe UI", size=10)

        # Variables
        self.doc_text_content = ""; self.transcript_text_content = ""; self.quotes_found = []
        self.doc_filepath = ""; self.transcript_filepath = ""; self.identify_speaker_var = BooleanVar(value=True)
        # self.context_menu_index = None # Removed context menu index

        # --- UI Layout (ttk widgets) ---
        top_frame = ttk.Frame(master, padding=(10, 8, 10, 5)); top_frame.pack(side=TOP, fill=X)
        self.load_doc_button = ttk.Button(top_frame, text="Load Document...", command=self.load_document); self.load_doc_button.pack(side=LEFT, padx=(0,5))
        self.load_transcript_button = ttk.Button(top_frame, text="Load Transcript...", command=self.load_transcript); self.load_transcript_button.pack(side=LEFT, padx=5)
        self.process_button = ttk.Button(top_frame, text="Find Quotes & Matches", command=self.process_texts, state=tk.DISABLED); self.process_button.pack(side=LEFT, padx=5)
        self.speaker_toggle_cb = ttk.Checkbutton(top_frame, text="Identify Speaker", variable=self.identify_speaker_var); self.speaker_toggle_cb.pack(side=LEFT, padx=(15, 5))
        self.status_label = ttk.Label(top_frame, text="Load files or paste text into the boxes below.", font=self.status_font); self.status_label.pack(side=LEFT, padx=10)

        main_content_frame = ttk.Frame(master, padding=(10, 5, 10, 10)); main_content_frame.pack(fill=BOTH, expand=True)
        self.main_pane = ttk.PanedWindow(main_content_frame, orient=tk.HORIZONTAL); self.main_pane.pack(fill=BOTH, expand=True)

        left_pane_container = ttk.Frame(self.main_pane, padding=0); self.main_pane.add(left_pane_container, weight=1)
        self.left_vertical_pane = ttk.PanedWindow(left_pane_container, orient=VERTICAL); self.left_vertical_pane.pack(fill=BOTH, expand=True)

        doc_pane_frame = ttk.Frame(self.left_vertical_pane, padding=2); self.doc_label = ttk.Label(doc_pane_frame, text="Document:", font=self.label_font); self.doc_label.pack(anchor='nw', pady=(0,3))
        self.doc_display = scrolledtext.ScrolledText( doc_pane_frame, wrap=tk.WORD, font=self.text_font, padx=5, pady=5, undo=True, spacing3=3); self.doc_display.pack(fill=BOTH, expand=True); self.doc_display.insert("1.0", "Paste Document text here or use 'Load Document...'"); self.left_vertical_pane.add(doc_pane_frame, weight=3)

        quote_list_pane_frame = ttk.Frame(self.left_vertical_pane, padding=2)

        # <<< Create Frame for Quote List Header (Label + Buttons) >>>
        quote_list_header_frame = ttk.Frame(quote_list_pane_frame)
        quote_list_header_frame.pack(fill=X, pady=(5,3)) # Fill horizontally, add padding

        self.quote_list_label = ttk.Label(quote_list_header_frame, text="Found Quotes:", font=self.label_font)
        self.quote_list_label.pack(side=LEFT, anchor='w') # Pack label to the left

        # <<< Add Flag/Unflag Buttons >>>
        self.unflag_button = ttk.Button(quote_list_header_frame, text="Unflag Sel.", command=self._unflag_selected_quote, state=tk.DISABLED, width=10) # Smaller width
        self.unflag_button.pack(side=RIGHT, padx=(2,0)) # Pack buttons to the right
        self.flag_button = ttk.Button(quote_list_header_frame, text="Flag Sel. (*)", command=self._flag_selected_quote, state=tk.DISABLED, width=10) # Smaller width
        self.flag_button.pack(side=RIGHT, padx=(5,2)) # Add padding between buttons

        listbox_container = tkFrame(quote_list_pane_frame); listbox_container.pack(fill=BOTH, expand=True)
        list_scrollbar = ttk.Scrollbar(listbox_container, orient=VERTICAL); list_scrollbar.pack(side=RIGHT, fill=Y)
        self.quote_listbox = Listbox( listbox_container, yscrollcommand=list_scrollbar.set, font=self.list_font, exportselection=False, selectbackground=LISTBOX_SELECT_BG, selectforeground=LISTBOX_SELECT_FG, borderwidth=0, highlightthickness=0); self.quote_listbox.pack(side=LEFT, fill=BOTH, expand=True); list_scrollbar.config(command=self.quote_listbox.yview);
        # <<< Bind selection change to update button states >>>
        self.quote_listbox.bind('<<ListboxSelect>>', self.on_quote_select)
        # <<< Removed right-click bindings >>>
        self.left_vertical_pane.add(quote_list_pane_frame, weight=1)

        right_frame = ttk.Frame(self.main_pane, padding=2); self.main_pane.add(right_frame, weight=1); self.transcript_label = ttk.Label(right_frame, text="Transcript:", font=self.label_font); self.transcript_label.pack(anchor='nw', pady=(0,3))
        self.transcript_display = scrolledtext.ScrolledText( right_frame, wrap=tk.WORD, font=self.text_font, padx=5, pady=5, undo=True, spacing3=3); self.transcript_display.pack(fill=BOTH, expand=True); self.transcript_display.insert("1.0", "Paste Transcript text here or use 'Load Transcript...'")

        bottom_frame = ttk.Frame(master, padding=(10, 10)); bottom_frame.pack(side=BOTTOM, fill=X)
        self.info_speaker_label = ttk.Label(bottom_frame, text="Speaker:", font=self.info_label_font); self.info_speaker_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font)
        self.info_status_label = ttk.Label(bottom_frame, text="Status:", font=self.info_label_font); self.info_status_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font)
        self.info_ratio_label = ttk.Label(bottom_frame, text="Ratio:", font=self.info_label_font); self.info_ratio_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font)
        self.info_pos_label = ttk.Label(bottom_frame, text="Positions:", font=self.info_label_font); self.info_pos_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font)
        self.info_quote_label = ttk.Label(bottom_frame, text="Quote (Doc):", font=self.info_label_font); self.info_quote_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font, wraplength=550)
        self.info_match_label = ttk.Label(bottom_frame, text="Match (Trans):", font=self.info_label_font); self.info_match_val_label = ttk.Label(bottom_frame, text="-", font=self.info_value_font, wraplength=550)
        pad_y_info = (0, 2)
        self.info_speaker_label.grid(row=0, column=0, sticky=W, padx=(0, 5), pady=pad_y_info); self.info_speaker_val_label.grid(row=0, column=1, sticky=W, pady=pad_y_info)
        self.info_status_label.grid(row=1, column=0, sticky=W, padx=(0, 5), pady=pad_y_info); self.info_status_val_label.grid(row=1, column=1, sticky=W, pady=pad_y_info)
        self.info_ratio_label.grid(row=2, column=0, sticky=W, padx=(0, 5), pady=pad_y_info); self.info_ratio_val_label.grid(row=2, column=1, sticky=W, pady=pad_y_info)
        self.info_pos_label.grid(row=3, column=0, sticky=W, padx=(0, 5), pady=pad_y_info); self.info_pos_val_label.grid(row=3, column=1, sticky=W, pady=pad_y_info)
        self.info_quote_label.grid(row=4, column=0, sticky=W+tk.N, padx=(0, 5), pady=pad_y_info); self.info_quote_val_label.grid(row=4, column=1, sticky=W, pady=pad_y_info)
        self.info_match_label.grid(row=5, column=0, sticky=W+tk.N, padx=(0, 5), pady=pad_y_info); self.info_match_val_label.grid(row=5, column=1, sticky=W, pady=pad_y_info)
        bottom_frame.columnconfigure(1, weight=1)

        # --- Tag Configurations ---
        self.doc_display.tag_configure("highlight_doc", background=HIGHLIGHT_COLOR_DOC)
        self.transcript_display.tag_configure("highlight_transcript_good", background=HIGHLIGHT_COLOR_TRANSCRIPT_GOOD)
        self.transcript_display.tag_configure("highlight_transcript_low", background=HIGHLIGHT_COLOR_TRANSCRIPT_LOW)

        # --- Bindings ---
        self.doc_display.bind("<<Modified>>", self._check_content_modified); self.transcript_display.bind("<<Modified>>", self._check_content_modified)
        for widget in [self.doc_display, self.transcript_display]:
            widget.bind("<Control-a>", self._select_all); widget.bind("<Control-A>", self._select_all)
            widget.bind("<Control-z>", self._undo); widget.bind("<Control-Z>", self._undo)
            widget.bind("<Control-y>", self._redo); widget.bind("<Control-Y>", self._redo)

        # <<< Removed context menu creation >>>

# --- Action Handlers for Bindings ---

    # <<< CORRECTED Multi-line format >>>
    def _select_all(self, event):
        widget = event.widget
        widget.tag_add(SEL, "1.0", END)
        widget.mark_set(INSERT, "1.0")
        widget.see(INSERT)
        return "break"

    # <<< CORRECTED Multi-line format >>>
    def _undo(self, event):
        widget = event.widget
        try:
            widget.edit_undo()
        except TclError: # Raised if undo stack is empty
            pass # Do nothing if nothing to undo
        return "break" # Important: Prevents default class binding

    # <<< CORRECTED Multi-line format >>>
    def _redo(self, event):
        widget = event.widget
        try:
            widget.edit_redo()
        except TclError: # Raised if redo stack is empty
            pass # Do nothing if nothing to redo
        return "break" # Important: Prevents default class binding
    # --- Flag Button Handlers ---
    # <<< Removed _show_listbox_menu >>>

    # <<< MODIFIED: Accepts index directly >>>
    def _set_flag_status(self, index, flagged_status):
        """Sets the flagged status for the quote at the given index."""
        if index is None or index < 0 or index >= len(self.quotes_found):
            return # No valid index

        try:
            quote_info = self.quotes_found[index]
            quote_info["flagged"] = flagged_status
            # <<< Call RENAMED helper function >>>
            self._refresh_listbox_item_display(index, quote_info=quote_info)
            # Update button states after changing flag
            self._update_flag_button_states(index)
        except IndexError:
            print(f"Error: Index {index} out of range for flagging.")

    # <<< MODIFIED: Gets index from current selection >>>
    def _flag_selected_quote(self):
        """Handler for 'Flag Selected' button."""
        selected_indices = self.quote_listbox.curselection()
        if not selected_indices:
            return # Nothing selected
        index = selected_indices[0]
        self._set_flag_status(index, True)

    # <<< MODIFIED: Gets index from current selection >>>
    def _unflag_selected_quote(self):
        """Handler for 'Unflag Selected' button."""
        selected_indices = self.quote_listbox.curselection()
        if not selected_indices:
            return # Nothing selected
        index = selected_indices[0]
        self._set_flag_status(index, False)

    # --- Other Methods ---
    def _check_content_modified(self, event=None):
        # ... (logic unchanged) ...
        if event: event.widget.edit_modified(False)
        doc_content = self.doc_display.get("1.0", "end-1c").strip(); transcript_content = self.transcript_display.get("1.0", "end-1c").strip()
        is_doc_placeholder = doc_content == "Paste Document text here or use 'Load Document...'"
        is_transcript_placeholder = transcript_content == "Paste Transcript text here or use 'Load Transcript...'"
        if doc_content and transcript_content and not is_doc_placeholder and not is_transcript_placeholder: self.process_button.config(state=tk.NORMAL)
        else: self.process_button.config(state=tk.DISABLED)

    def _load_file(self, text_widget, label_widget, placeholder_text, title):
        # ... (logic unchanged) ...
        filepath = filedialog.askopenfilename(title=title, filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]);
        if not filepath: return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            text_widget.delete("1.0", END); text_widget.insert("1.0", content); label_widget.config(text=f"{title.split(' ')[1]}: {os.path.basename(filepath)}")
            text_widget.edit_reset(); text_widget.edit_modified(True); return filepath, content
        except Exception as e:
            messagebox.showerror("Error Reading File", f"Failed to read file: {filepath}\n{e}")
            text_widget.delete("1.0", END); text_widget.insert("1.0", placeholder_text); label_widget.config(text=f"{title.split(' ')[1]}:")
            text_widget.edit_reset(); text_widget.edit_modified(True); return None

    def load_document(self):
        # ... (logic unchanged) ...
        result = self._load_file(self.doc_display, self.doc_label, "Paste Document text here or use 'Load Document...'", "Select Document File")
        if result: self.doc_filepath, self.doc_text_content = result; self.status_label.config(text=f"Loaded Document: {os.path.basename(self.doc_filepath)}")

    def load_transcript(self):
        # ... (logic unchanged) ...
        result = self._load_file(self.transcript_display, self.transcript_label, "Paste Transcript text here or use 'Load Transcript...'", "Select Transcript File")
        if result:
            self.transcript_filepath, self.transcript_text_content = result; doc_status = f"Doc: {os.path.basename(self.doc_filepath)}" if self.doc_filepath else "Doc: (Pasted/None)"
            self.status_label.config(text=f"{doc_status}, Loaded Transcript: {os.path.basename(self.transcript_filepath)}")

    def process_texts(self):
        """Finds quotes, matches, and optionally speakers."""
        # ... (Get text, validation - unchanged) ...
        self.doc_text_content = self.doc_display.get("1.0", END).strip(); self.transcript_text_content = self.transcript_display.get("1.0", END).strip()
        if not self.doc_text_content or self.doc_text_content == "Paste Document text here or use 'Load Document...'": messagebox.showwarning("Missing Text", "Document text is empty or placeholder."); return
        if not self.transcript_text_content or self.transcript_text_content == "Paste Transcript text here or use 'Load Transcript...'": messagebox.showwarning("Missing Text", "Transcript text is empty or placeholder."); return

        self.status_label.config(text="Processing..."); self.master.update_idletasks()
        # Disable flag buttons before clearing list
        self.flag_button.config(state=tk.DISABLED)
        self.unflag_button.config(state=tk.DISABLED)
        self.quote_listbox.delete(0, END); self.doc_display.tag_remove("highlight_doc", "1.0", END); self.transcript_display.tag_remove("highlight_transcript_good", "1.0", END); self.transcript_display.tag_remove("highlight_transcript_low", "1.0", END)
        self._clear_info_labels()

        # Check speaker toggle state
        identify_speakers = self.identify_speaker_var.get()

        # Pre-calculate speaker positions if enabled
        transcript_speaker_positions = []
        if identify_speakers:
            print("DEBUG: Pre-calculating speaker positions...") # DEBUG
            for match in re.finditer(r'\[(.*?)\]', self.transcript_text_content, re.DOTALL):
                speaker_name = match.group(1).strip();
                if speaker_name: transcript_speaker_positions.append({"name": speaker_name, "end_pos": match.end()})
            print(f"DEBUG: Found {len(transcript_speaker_positions)} speaker tags.") # DEBUG

        # Find quotes in DOCUMENT
        print("DEBUG: Calling find_quotes...") # DEBUG (already confirmed working)
        self.quotes_found = find_quotes(self.doc_text_content)
        print(f"DEBUG: Found {len(self.quotes_found)} quotes.") # DEBUG (already confirmed working)

        if not self.quotes_found:
             messagebox.showinfo("No Quotes", "No text within double quotes was found in the document."); self.status_label.config(text="Processing complete. No quotes found in document."); self._clear_info_labels(); return

# ... inside process_texts ...
        match_count, low_match_count, no_match_count = 0, 0, 0
        # print(f"DEBUG: Starting loop through {len(self.quotes_found)} quotes...") # Can remove debug prints now
        for i, quote_info in enumerate(self.quotes_found):
            # print(f"\nDEBUG: --- Iteration {i} ---")
            # try: # Can remove debug try/except now
            quote_text = quote_info["text"]
            match_result = find_best_match(quote_text, self.transcript_text_content)
            quote_info["match"] = match_result

            # Find Speaker if enabled
            speaker = None
            if identify_speakers:
                 speaker = "[Unknown Speaker]"
                 if match_result:
                      transcript_match_start = match_result["transcript_start"]; latest_speaker_pos, found_speaker_name = -1, None
                      for sp in transcript_speaker_positions:
                           if sp["end_pos"] < transcript_match_start and sp["end_pos"] > latest_speaker_pos: latest_speaker_pos, found_speaker_name = sp["end_pos"], sp["name"]
                      if found_speaker_name: speaker = f"[{found_speaker_name}]"
                 else: speaker = "[No Transcript Match]"
            quote_info["speaker"] = speaker

            # Determine status description and color
            status_description = "No Match Found"
            if match_result:
                if match_result["ratio"] >= MATCH_THRESHOLD: fg_color, status_description = 'darkgreen', "Good Match"; match_count += 1
                else: fg_color, status_description = 'darkorange', "Low Match"; low_match_count += 1
            else: fg_color, status_description = 'red', "No Match Found"; no_match_count += 1
            quote_info["status_description"] = status_description

            # <<< MODIFIED: Direct Insert/Config instead of calling helper >>>
            # Build list entry string (including flag status)
            is_flagged = quote_info.get("flagged", False) # Should be False initially
            flag_prefix = FLAG_INDICATOR if is_flagged else ""
            speaker_prefix = f"{speaker} " if speaker else ""
            list_entry = f"{flag_prefix}{speaker_prefix}{quote_text[:70]}{'...' if len(quote_text)>70 else ''}"

            # Insert directly into listbox
            self.quote_listbox.insert(END, list_entry) # Use END for initial population

            # Configure colors directly
            row_bg = LISTBOX_EVEN_ROW_BG if i % 2 == 0 else LISTBOX_ODD_ROW_BG
            # Use END index here as well for itemconfig after insert(END, ...)
            self.quote_listbox.itemconfig(END, {'fg': fg_color, 'bg': row_bg})
            # <<< END MODIFICATION >>>

            # except Exception as e: # Remove debug try/except
            #     # ... error handling ...

            # Periodic GUI Update
            if (i + 1) % 10 == 0:
                 # print(f"DEBUG: Updating status label at iteration {i}")
                 self.status_label.config(text=f"Processing... Analyzed {i+1}/{len(self.quotes_found)} quotes.");
                 self.master.update_idletasks()

        # print("DEBUG: Finished loop through quotes.")
        # Final status update
        self.status_label.config(text=f"Done. Quotes: {len(self.quotes_found)} | Good: {match_count} | Low: {low_match_count} | None: {no_match_count}")

    def on_quote_select(self, event):
        """Highlights selected quote/match, shows info, updates flag buttons."""
        selected_indices = self.quote_listbox.curselection()
        if not selected_indices:
            self._clear_info_labels()
            # <<< Disable buttons if nothing selected >>>
            self.flag_button.config(state=tk.DISABLED)
            self.unflag_button.config(state=tk.DISABLED)
            return

        selected_index = selected_indices[0]
        if selected_index < 0 or selected_index >= len(self.quotes_found):
            self._clear_info_labels()
            self.flag_button.config(state=tk.DISABLED)
            self.unflag_button.config(state=tk.DISABLED)
            return

        selected_quote_info = self.quotes_found[selected_index]

        # --- Update Highlights ---
        self.doc_display.tag_remove("highlight_doc", "1.0", END); self.transcript_display.tag_remove("highlight_transcript_good", "1.0", END); self.transcript_display.tag_remove("highlight_transcript_low", "1.0", END)
        doc_start, doc_end = selected_quote_info.get('start', -1), selected_quote_info.get('end', -1)
        if doc_start != -1 and doc_end != -1:
             doc_start_idx, doc_end_idx = f"1.0+{doc_start}c", f"1.0+{doc_end}c"; self.doc_display.tag_add("highlight_doc", doc_start_idx, doc_end_idx); self.doc_display.see(doc_start_idx)

        # --- Update Info Labels ---
        speaker = selected_quote_info.get("speaker"); status_text = selected_quote_info.get("status_description", "-")
        quote_display_text = selected_quote_info.get('text', ''); match_result = selected_quote_info.get("match")
        self.info_speaker_val_label.config(text=speaker if speaker is not None else "Disabled"); self.info_status_val_label.config(text=status_text)
        ratio_text = "-"; pos_text = f"Doc: {doc_start}-{doc_end} | Transcript: -" ; match_display_text = "-"
        if match_result:
            t_start, t_end = match_result.get("transcript_start", -1), match_result.get("transcript_end", -1); ratio, matched_text = match_result.get("ratio", 0.0), match_result.get("matched_text", "")
            ratio_text = f"{ratio:.1%}"; pos_text = f"Doc: {doc_start}-{doc_end} | Transcript: {t_start}-{t_end}"; match_display_text = matched_text
            if t_start != -1 and t_end != -1 and t_end >= t_start:
                 t_start_idx, t_end_idx = f"1.0+{t_start}c", f"1.0+{t_end}c"; tag_to_use = "highlight_transcript_good" if ratio >= MATCH_THRESHOLD else "highlight_transcript_low"
                 self.transcript_display.tag_add(tag_to_use, t_start_idx, t_end_idx); self.transcript_display.see(t_start_idx)
        self.info_ratio_val_label.config(text=ratio_text); self.info_pos_val_label.config(text=pos_text); self.info_quote_val_label.config(text=quote_display_text); self.info_match_val_label.config(text=match_display_text)

        # --- Update Flag Button States ---
        self._update_flag_button_states(selected_index)


    def _clear_info_labels(self):
        """Resets the info labels and disables flag buttons."""
        self.info_speaker_val_label.config(text="-"); self.info_status_val_label.config(text="-"); self.info_ratio_val_label.config(text="-"); self.info_pos_val_label.config(text="-"); self.info_quote_val_label.config(text="-"); self.info_match_val_label.config(text="-")
        # <<< Disable buttons when info is cleared >>>
        self.flag_button.config(state=tk.DISABLED)
        self.unflag_button.config(state=tk.DISABLED)

# <<< RENAMED HELPER >>>
    def _refresh_listbox_item_display(self, index, quote_info=None, fg_color=None):
         """Refreshes the text and colors of a specific listbox item (e.g., after flagging)."""
         # Check against the data source length first
         if quote_info is None:
             if index < 0 or index >= len(self.quotes_found): return
             quote_info = self.quotes_found[index]

         # Determine foreground color if not provided (needed if called only with index)
         if fg_color is None:
             match_result = quote_info.get("match")
             if match_result:
                 fg_color = 'darkgreen' if match_result["ratio"] >= MATCH_THRESHOLD else 'darkorange'
             else:
                 fg_color = 'red'

         # Get other data needed for the entry string
         speaker = quote_info.get("speaker")
         quote_text = quote_info.get("text", "")
         is_flagged = quote_info.get("flagged", False)

         # Build list entry string
         flag_prefix = FLAG_INDICATOR if is_flagged else ""
         speaker_prefix = f"{speaker} " if speaker else ""
         list_entry = f"{flag_prefix}{speaker_prefix}{quote_text[:70]}{'...' if len(quote_text)>70 else ''}" # Use consistent length

         # Determine background color for alternating rows
         row_bg = LISTBOX_EVEN_ROW_BG if index % 2 == 0 else LISTBOX_ODD_ROW_BG

         # Update the item in the listbox using DELETE and INSERT
         current_selection = self.quote_listbox.curselection() # Remember selection
         try:
             # This delete/insert is appropriate for an *update* action
             self.quote_listbox.delete(index)
             self.quote_listbox.insert(index, list_entry)
             self.quote_listbox.itemconfig(index, {'fg': fg_color, 'bg': row_bg})

             # Restore selection if it was this item
             if current_selection and current_selection[0] == index:
                 self.quote_listbox.selection_set(index)
         except tk.TclError as e:
             print(f"ERROR in _refresh_listbox_item_display trying to update item at index {index}: {e}")
             
    def _update_flag_button_states(self, selected_index):
        """Enables/Disables flag buttons based on the selected item's state."""
        if selected_index < 0 or selected_index >= len(self.quotes_found):
            self.flag_button.config(state=tk.DISABLED)
            self.unflag_button.config(state=tk.DISABLED)
            return

        is_flagged = self.quotes_found[selected_index].get("flagged", False)
        self.flag_button.config(state=tk.DISABLED if is_flagged else tk.NORMAL)
        self.unflag_button.config(state=tk.NORMAL if is_flagged else tk.DISABLED)
        print("DEBUG: Finished loop through quotes.") # DEBUG

# --- Run the App ---
if __name__ == "__main__":
    root = tk.Tk()
    app = QuoteCheckerApp(root)
    root.mainloop()
