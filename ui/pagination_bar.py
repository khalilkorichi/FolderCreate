"""
ui/pagination_bar.py
───────────────────
Reusable, sleek RTL Pagination Component:
- Allows smooth multi-page navigation across lists and grids.
- Prevents UI freezes by bounding rendered widgets to page size.
- Rubik typography & Arabic RTL layout.
"""

import customtkinter as ctk
from typing import Callable


class PaginationBar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        total_items: int = 0,
        page_size: int = 10,
        on_page_change: Callable[[int], None] = None,
        fg_color: str = "transparent"
    ):
        super().__init__(parent, fg_color=fg_color)
        self.total_items = max(0, total_items)
        self.page_size = max(1, page_size)
        self.current_page = 1
        self.on_page_change = on_page_change

        self._build_ui()
        self.update_state(self.total_items, self.page_size)

    def _build_ui(self):
        # RTL Layout: Next on left, Prev on right, Page details in center
        self.inner = ctk.CTkFrame(self, fg_color=("gray90", "gray17"), corner_radius=8)
        self.inner.pack(fill="x", padx=10, pady=4)

        # Right side: Previous Page Button (In RTL, going forward in pages is left, previous is right)
        self.prev_btn = ctk.CTkButton(
            self.inner,
            text="▶ السابق",
            width=75,
            height=28,
            font=("Rubik", 10, "bold"),
            fg_color=("gray75", "gray28"),
            hover_color=("gray65", "gray22"),
            command=self._prev_page
        )
        self.prev_btn.pack(side="right", padx=(8, 4), pady=5)

        # Center: Info & page status
        self.info_lbl = ctk.CTkLabel(
            self.inner,
            text="صفحة 1 من 1",
            font=("Rubik", 11, "bold"),
            text_color=("gray20", "gray85")
        )
        self.info_lbl.pack(side="right", expand=True, padx=10)

        # Left side: Next Page Button
        self.next_btn = ctk.CTkButton(
            self.inner,
            text="التالي ◀",
            width=75,
            height=28,
            font=("Rubik", 10, "bold"),
            fg_color=("gray75", "gray28"),
            hover_color=("gray65", "gray22"),
            command=self._next_page
        )
        self.next_btn.pack(side="left", padx=(4, 8), pady=5)

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 1
        return (self.total_items + self.page_size - 1) // self.page_size

    def update_state(self, total_items: int, page_size: int = None, reset_to_first: bool = False):
        self.total_items = max(0, total_items)
        if page_size:
            self.page_size = max(1, page_size)

        if reset_to_first or self.current_page > self.total_pages:
            self.current_page = 1

        self.current_page = max(1, min(self.current_page, self.total_pages))

        # Update button enable/disable states
        self.prev_btn.configure(state="normal" if self.current_page > 1 else "disabled")
        self.next_btn.configure(state="normal" if self.current_page < self.total_pages else "disabled")

        start_idx = (self.current_page - 1) * self.page_size + 1 if self.total_items > 0 else 0
        end_idx = min(self.current_page * self.page_size, self.total_items)

        self.info_lbl.configure(
            text=f"صفحة {self.current_page} من {self.total_pages}  ({start_idx}-{end_idx} من إجمالي {self.total_items})"
        )

        # Hide bar completely if items fit on 1 page and total is 0
        if self.total_pages <= 1 and self.total_items <= self.page_size:
            self.prev_btn.configure(state="disabled")
            self.next_btn.configure(state="disabled")

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_state(self.total_items)
            if self.on_page_change:
                self.on_page_change(self.current_page)

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_state(self.total_items)
            if self.on_page_change:
                self.on_page_change(self.current_page)

    def get_slice(self, items: list) -> list:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return items[start:end]
