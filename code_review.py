import tkinter as tk
import customtkinter as ctk
import difflib
from pygments import highlight
from pygments.lexers import get_lexer_for_filename, Python3Lexer
from pygments.formatters import HtmlFormatter

class CodeReviewDialog(ctk.CTkToplevel):
    """Dialog window for reviewing code changes with GitHub-style diff display"""
    
    def __init__(self, parent, file_path, old_code, new_code, line_num=None, 
                 on_accept=None, on_reject=None, theme=None):
        """
        Initialize the code review dialog.
        
        Args:
            parent: Parent window
            file_path: Path to the file being modified
            old_code: Original code content 
            new_code: New code content
            line_num: Line number to highlight (optional)
            on_accept: Callback function when changes are accepted
            on_reject: Callback function when changes are rejected
            theme: Theme colors for styling
        """
        super().__init__(parent)
        self.title(f"Code Review: {file_path}")
        self.geometry("900x600")
        self.resizable(True, True)
        
        # Store parameters
        self.parent = parent
        self.file_path = file_path
        self.old_code = old_code
        self.new_code = new_code
        self.line_num = line_num
        self.on_accept = on_accept
        self.on_reject = on_reject
        self.theme = theme or self._default_theme()
        
        # Configure the dialog
        self.configure(fg_color=self.theme.BACKGROUND)
        
        # Setup UI
        self._create_ui()
        
        # Make dialog modal
        self.grab_set()
        self.focus_set()
        
    def _default_theme(self):
        """Default theme if none provided"""
        # Simple theme structure with essential colors
        class SimpleTheme:
            BACKGROUND = "#1F1F28"
            FOREGROUND = "#DCD7BA"
            DARKER_BG = "#16161D"
            LIGHTER_BG = "#2A2A37"
            SELECTION = "#2D4F67"
            ADDITION = "#98BB6C"  # Green for additions
            DELETION = "#E82424"  # Red for deletions
            BUTTON_BG = "#2A2A37"
            BUTTON_HOVER = "#363646"
            BUTTON_ACCEPT = "#7AA89F"  # Soft green for accept button
            BUTTON_REJECT = "#C34043"  # Soft red for reject button
            
        return SimpleTheme
    
    def _create_ui(self):
        """Create the UI components"""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with file info
        header_frame = ctk.CTkFrame(self, fg_color=self.theme.DARKER_BG, height=40)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        
        file_label = ctk.CTkLabel(
            header_frame, 
            text=f"Reviewing changes to: {self.file_path}",
            text_color=self.theme.FOREGROUND,
            font=("Arial", 12, "bold")
        )
        file_label.pack(side="left", padx=10, pady=10)
        
        # If we have a line number, show it
        if self.line_num:
            line_label = ctk.CTkLabel(
                header_frame,
                text=f"Line: {self.line_num}",
                text_color=self.theme.FOREGROUND,
                font=("Arial", 10)
            )
            line_label.pack(side="left", padx=10, pady=10)
        
        # Content frame with diff view
        content_frame = ctk.CTkFrame(self, fg_color=self.theme.BACKGROUND)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # We'll create a custom diff view
        self.diff_view = DiffView(content_frame, self.old_code, self.new_code, self.theme)
        self.diff_view.pack(fill="both", expand=True)
        
        # Action buttons at the bottom
        button_frame = ctk.CTkFrame(self, fg_color=self.theme.DARKER_BG, height=50)
        button_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        
        # Cancel button (rejects changes)
        reject_btn = ctk.CTkButton(
            button_frame,
            text="Reject Changes",
            fg_color=self.theme.BUTTON_REJECT,
            hover_color="#D54C4C",  # Slightly brighter red on hover
            text_color=self.theme.FOREGROUND,
            width=150,
            height=32,
            command=self._reject_changes
        )
        reject_btn.pack(side="left", padx=15, pady=10)
        
        # Accept button
        accept_btn = ctk.CTkButton(
            button_frame,
            text="Accept Changes",
            fg_color=self.theme.BUTTON_ACCEPT,
            hover_color="#8BC49D",  # Slightly brighter green on hover
            text_color=self.theme.FOREGROUND,
            width=150,
            height=32,
            command=self._accept_changes
        )
        accept_btn.pack(side="right", padx=15, pady=10)
    
    def _accept_changes(self):
        """Accept the code changes and close dialog"""
        if self.on_accept:
            self.on_accept(self.new_code)
        self.destroy()
    
    def _reject_changes(self):
        """Reject the code changes and close dialog"""
        if self.on_reject:
            self.on_reject()
        self.destroy()


class DiffView(ctk.CTkFrame):
    """Custom widget for displaying code diffs in GitHub-like style"""
    
    def __init__(self, parent, old_code, new_code, theme):
        """
        Initialize the diff view.
        
        Args:
            parent: Parent widget
            old_code: Original code content
            new_code: New code content
            theme: Theme colors for styling
        """
        super().__init__(parent, fg_color=theme.LIGHTER_BG, corner_radius=5)
        
        self.old_code = old_code
        self.new_code = new_code
        self.theme = theme
        
        # Split code into lines
        self.old_lines = old_code.splitlines()
        self.new_lines = new_code.splitlines()
        
        # Configure the frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create diff display
        self._create_diff_display()
    
    def _create_diff_display(self):
        """Create the diff display with syntax highlighting"""
        # Scrollable container for diff
        scroll_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color=self.theme.LIGHTER_BG,
            scrollbar_fg_color=self.theme.DARKER_BG,
            scrollbar_button_hover_color=self.theme.FOREGROUND
        )
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        # Generate the diff
        diff = difflib.unified_diff(
            self.old_lines,
            self.new_lines,
            lineterm='',
            n=3  # Context lines
        )
        
        # Process and display the diff lines
        current_section = None
        section_frame = None
        
        for i, line in enumerate(diff):
            # Skip the first two lines (diff header)
            if i < 2:
                continue
            
            # Skip chunk header lines
            if line.startswith('@@'):
                if section_frame:
                    # Add a separator between sections
                    separator = ctk.CTkFrame(
                        scroll_frame, 
                        fg_color=self.theme.DARKER_BG, 
                        height=2
                    )
                    separator.pack(fill="x", pady=5)
                
                # Create a new section frame
                section_frame = ctk.CTkFrame(
                    scroll_frame, 
                    fg_color=self.theme.LIGHTER_BG
                )
                section_frame.pack(fill="x", padx=0, pady=5)
                
                # Create section header
                header = ctk.CTkLabel(
                    section_frame,
                    text=line,
                    text_color=self.theme.FOREGROUND,
                    font=("Consolas", 10),
                    anchor="w",
                    fg_color=self.theme.DARKER_BG
                )
                header.pack(fill="x", padx=0, pady=0)
                
                current_section = section_frame
                continue
            
            # Skip if we don't have a section yet
            if not section_frame:
                continue
            
            # Determine line type and create styled line
            line_frame = ctk.CTkFrame(
                section_frame, 
                fg_color="transparent",
                height=20
            )
            line_frame.pack(fill="x", padx=0, pady=0)
            
            # Line number placeholder (left)
            line_num = ctk.CTkLabel(
                line_frame,
                text="   ",
                text_color=self.theme.FOREGROUND,
                font=("Consolas", 10),
                width=30
            )
            line_num.pack(side="left", padx=(0, 5))
            
            # Line content
            if line.startswith('+'):
                # Addition line
                content = ctk.CTkLabel(
                    line_frame,
                    text=line,
                    text_color=self.theme.ADDITION,
                    font=("Consolas", 11),
                    anchor="w",
                    fg_color=self.theme.LIGHTER_BG
                )
                content.pack(fill="x", padx=0, pady=0, side="left", expand=True)
            elif line.startswith('-'):
                # Deletion line
                content = ctk.CTkLabel(
                    line_frame,
                    text=line,
                    text_color=self.theme.DELETION,
                    font=("Consolas", 11),
                    anchor="w",
                    fg_color=self.theme.LIGHTER_BG
                )
                content.pack(fill="x", padx=0, pady=0, side="left", expand=True)
            else:
                # Context line
                content = ctk.CTkLabel(
                    line_frame,
                    text=line,
                    text_color=self.theme.FOREGROUND,
                    font=("Consolas", 11),
                    anchor="w"
                )
                content.pack(fill="x", padx=0, pady=0, side="left", expand=True)


def show_code_review(parent, file_path, old_code, new_code, line_num=None, on_accept=None, on_reject=None, theme=None):
    """
    Show a code review dialog with GitHub-style diff view.
    
    Args:
        parent: Parent window
        file_path: Path to the file being modified
        old_code: Original code content
        new_code: New code content
        line_num: Line number to highlight (optional)
        on_accept: Callback when changes are accepted
        on_reject: Callback when changes are rejected
        theme: Theme colors for styling
    
    Returns:
        The dialog instance
    """
    dialog = CodeReviewDialog(
        parent, file_path, old_code, new_code, line_num, on_accept, on_reject, theme
    )
    return dialog 