#!/usr/bin/env python3
"""
Textual Graph Plotting Application
Supports: PlotWidget (in-terminal), Matplotlib (external window), Sixel (terminal graphics)
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
import subprocess
from typing import Optional

from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Header, Footer, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual import work

# ============================================================================
# Feature Detection
# ============================================================================

HAS_PLOTWIDGET = False
HAS_MATPLOTLIB = False
HAS_PIL = False

try:
    from textual_plot import PlotWidget
    HAS_PLOTWIDGET = True
except ImportError:
    PlotWidget = None  # type: ignore

try:
    import matplotlib
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    matplotlib = None  # type: ignore
    plt = None  # type: ignore

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    Image = None  # type: ignore


# ============================================================================
# Sample Data
# ============================================================================

SAMPLE_X = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SAMPLE_Y = [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100]  # y = x²


# ============================================================================
# Sixel Converter (No external sixel libraries)
# ============================================================================

class SixelConverter:
    """
    Convert images to Sixel format without external sixel libraries.
    Only requires PIL/Pillow for image processing.
    """
    
    @staticmethod
    def png_bytes_to_sixel(
        png_data: bytes, 
        max_width: int = 600, 
        max_height: int = 300,
        num_colors: int = 64
    ) -> str:
        """
        Convert PNG bytes to Sixel string.
        
        Sixel format encodes 6 vertical pixels per character.
        Each character is calculated as: chr(63 + bitmap_value)
        where bitmap_value is a 6-bit value (bits 0-5 represent rows 0-5).
        """
        if not HAS_PIL:
            raise ImportError("PIL/Pillow required for sixel conversion")
        
        from PIL import Image
        from io import BytesIO
        
        # Load and prepare image
        img = Image.open(BytesIO(png_data))
        img = img.convert('RGB')
        
        # Resize if needed
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        width, height = img.size
        
        # Quantize to limited palette
        img_quantized = img.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
        palette_data = img_quantized.getpalette()[:num_colors * 3]
        indexed_pixels = list(img_quantized.getdata())
        
        # Build sixel output
        parts = []
        
        # DCS (Device Control String) introducer: ESC P q
        parts.append('\x1bPq')
        
        # Raster attributes: "Pan;Pad;Ph;Pv"
        parts.append(f'"1;1;{width};{height}')
        
        # Define color palette
        # Format: #Pc;Pu;Px;Py;Pz (Pc=color#, Pu=2 for RGB, Px/Py/Pz=R/G/B 0-100)
        for i in range(num_colors):
            r = palette_data[i * 3] * 100 // 255
            g = palette_data[i * 3 + 1] * 100 // 255
            b = palette_data[i * 3 + 2] * 100 // 255
            parts.append(f'#{i};2;{r};{g};{b}')
        
        # Generate sixel data (6 rows per band)
        for band_y in range(0, height, 6):
            # Find colors used in this band
            colors_used = set()
            for bit in range(6):
                y = band_y + bit
                if y < height:
                    for x in range(width):
                        colors_used.add(indexed_pixels[y * width + x])
            
            first_color_in_band = True
            for color_idx in sorted(colors_used):
                # Carriage return ($) for same band, different color
                if not first_color_in_band:
                    parts.append('$')
                first_color_in_band = False
                
                # Select color
                parts.append(f'#{color_idx}')
                
                # Build row of sixel characters
                row_chars = []
                for x in range(width):
                    sixel_value = 0
                    for bit in range(6):
                        y = band_y + bit
                        if y < height:
                            pixel_color = indexed_pixels[y * width + x]
                            if pixel_color == color_idx:
                                sixel_value |= (1 << bit)
                    row_chars.append(chr(63 + sixel_value))
                
                # Apply RLE compression
                compressed = SixelConverter._rle_compress(''.join(row_chars))
                parts.append(compressed)
            
            # Graphics new line (-)
            parts.append('-')
        
        # String terminator: ESC \
        parts.append('\x1b\\')
        
        return ''.join(parts)
    
    @staticmethod
    def _rle_compress(data: str) -> str:
        """Run-length encode sixel data for compression."""
        if not data:
            return ''
        
        result = []
        i = 0
        
        while i < len(data):
            char = data[i]
            count = 1
            
            while i + count < len(data) and data[i + count] == char and count < 255:
                count += 1
            
            if count > 3:
                result.append(f'!{count}{char}')
            else:
                result.append(char * count)
            
            i += count
        
        return ''.join(result)


# ============================================================================
# Placeholder Widget
# ============================================================================

class PlotPlaceholder(Static):
    """Placeholder when PlotWidget is not available."""
    
    def __init__(self) -> None:
        super().__init__(
            "[bold yellow]PlotWidget not available[/]\n\n"
            "Install with: [cyan]pip install textual-plot[/]\n\n"
            "[dim]The plot will appear here when available.[/]"
        )


# ============================================================================
# Main Application
# ============================================================================

class GraphPlotterApp(App[None]):
    """Textual application for plotting graphs using different backends."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #plot-area {
        height: 1fr;
        border: double $primary;
        margin: 1;
        padding: 1;
    }
    
    #controls {
        height: auto;
        layout: horizontal;
        align: center middle;
        padding: 1;
        background: $surface;
        border: solid $secondary;
        margin: 0 1;
    }
    
    #controls Button {
        margin: 0 2;
        min-width: 24;
    }
    
    #status-bar {
        height: 3;
        content-align: center middle;
        background: $surface-darken-1;
        border: solid $primary-darken-1;
        margin: 1;
        padding: 0 1;
    }
    
    PlotPlaceholder {
        content-align: center middle;
        height: 100%;
    }
    
    .disabled-info {
        color: $text-muted;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("p", "refresh_plotwidget", "Refresh Plot"),
        Binding("m", "show_matplotlib", "Matplotlib"),
        Binding("s", "generate_sixel", "Sixel"),
    ]
    
    TITLE = "Graph Plotter"
    SUB_TITLE = "PlotWidget | Matplotlib | Sixel"
    
    def __init__(self) -> None:
        super().__init__()
        self.x_data = SAMPLE_X.copy()
        self.y_data = SAMPLE_Y.copy()
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Vertical(id="main-layout"):
            # Control buttons
            with Horizontal(id="controls"):
                if HAS_PLOTWIDGET:
                    yield Button(
                        "📊 Refresh PlotWidget", 
                        id="btn-plotwidget", 
                        variant="primary"
                    )
                else:
                    yield Button(
                        "📊 PlotWidget (N/A)", 
                        id="btn-plotwidget", 
                        disabled=True,
                        classes="disabled-info"
                    )
                
                # THE MATPLOTLIB "View Plot" BUTTON
                if HAS_MATPLOTLIB:
                    yield Button(
                        "📈 View Plot", 
                        id="btn-matplotlib", 
                        variant="success"
                    )
                else:
                    yield Button(
                        "📈 View Plot (N/A)", 
                        id="btn-matplotlib", 
                        disabled=True,
                        classes="disabled-info"
                    )
                
                yield Button(
                    "🖼️ Generate Sixel", 
                    id="btn-sixel", 
                    variant="warning"
                )
            
            # Plot display area
            with Container(id="plot-area"):
                if HAS_PLOTWIDGET:
                    yield PlotWidget(id="main-plot")
                else:
                    yield PlotPlaceholder()
            
            # Status bar
            yield Static("Ready. Select a plotting method.", id="status-bar")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the plot on mount."""
        self._refresh_plotwidget()
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _update_status(self, message: str) -> None:
        """Update the status bar text."""
        status = self.query_one("#status-bar", Static)
        status.update(message)
    
    def _refresh_plotwidget(self) -> None:
        """Update the PlotWidget with current data."""
        if not HAS_PLOTWIDGET:
            return
        
        try:
            plot_widget = self.query_one("#main-plot", PlotWidget)
            plot_widget.clear()
            plot_widget.plot(x=self.x_data, y=self.y_data)
            self._update_status("✓ PlotWidget displaying y = x²")
        except Exception as e:
            self._update_status(f"✗ PlotWidget error: {e}")
    
    # ========================================================================
    # Button Event Handler
    # ========================================================================
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events using callbacks."""
        button_id = event.button.id
        
        # Callback mapping
        callbacks = {
            "btn-plotwidget": self._on_plotwidget_clicked,
            "btn-matplotlib": self._on_matplotlib_clicked,
            "btn-sixel": self._on_sixel_clicked,
        }
        
        callback = callbacks.get(button_id)
        if callback:
            callback()
    
    # ========================================================================
    # Callback Functions
    # ========================================================================
    
    def _on_plotwidget_clicked(self) -> None:
        """Callback for PlotWidget button."""
        if not HAS_PLOTWIDGET:
            self.notify("PlotWidget not installed", severity="warning")
            return
        
        self._refresh_plotwidget()
        self.notify("PlotWidget refreshed!", title="Success")
    
    def _on_matplotlib_clicked(self) -> None:
        """Callback for Matplotlib 'View Plot' button."""
        if not HAS_MATPLOTLIB:
            self.notify(
                "Matplotlib not installed\nRun: pip install matplotlib",
                severity="error",
                title="Missing Dependency"
            )
            return
        
        self._update_status("⏳ Opening Matplotlib window...")
        self.notify("Opening Matplotlib window...", title="Matplotlib")
        self._show_matplotlib_window()
    
    def _on_sixel_clicked(self) -> None:
        """Callback for Sixel button."""
        self._update_status("⏳ Generating Sixel plot...")
        self.notify("Generating Sixel plot...", title="Sixel")
        self._generate_sixel_plot()
    
    # ========================================================================
    # Actions (keyboard bindings)
    # ========================================================================
    
    def action_refresh_plotwidget(self) -> None:
        """Action: Refresh PlotWidget."""
        self._on_plotwidget_clicked()
    
    def action_show_matplotlib(self) -> None:
        """Action: Show Matplotlib window."""
        self._on_matplotlib_clicked()
    
    def action_generate_sixel(self) -> None:
        """Action: Generate Sixel plot."""
        self._on_sixel_clicked()
    
    # ========================================================================
    # Worker Tasks (run in background thread)
    # ========================================================================
    
    @work(thread=True, exclusive=True, group="matplotlib")
    def _show_matplotlib_window(self) -> None:
        """Open matplotlib plot in external window (threaded)."""
        try:
            import matplotlib
            matplotlib.use('TkAgg')  # GUI backend
            import matplotlib.pyplot as plt
            
            # Create figure
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Plot data
            ax.plot(
                self.x_data, 
                self.y_data, 
                'b-o', 
                linewidth=2, 
                markersize=8, 
                label='y = x²'
            )
            
            # Styling
            ax.set_title('Graph: y = x²', fontsize=14, fontweight='bold')
            ax.set_xlabel('X', fontsize=12)
            ax.set_ylabel('Y', fontsize=12)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.legend(loc='upper left')
            ax.set_facecolor('#f5f5f5')
            fig.tight_layout()
            
            # Show window (blocks until closed)
            plt.show()
            
            # Update UI after window closes
            self.call_from_thread(
                self._update_status, 
                "✓ Matplotlib window closed"
            )
            
        except Exception as e:
            self.call_from_thread(
                self.notify, 
                f"Matplotlib error: {e}", 
                severity="error"
            )
            self.call_from_thread(
                self._update_status, 
                f"✗ Matplotlib error: {e}"
            )
    
    @work(thread=True, exclusive=True, group="sixel")
    def _generate_sixel_plot(self) -> None:
        """Generate sixel plot and save to file (threaded)."""
        output_path = "/tmp/graph_plot.sixel"
        
        try:
            if not HAS_MATPLOTLIB:
                self.call_from_thread(
                    self.notify,
                    "Matplotlib required for generating plot image",
                    severity="error"
                )
                return
            
            # Generate plot image
            import matplotlib
            matplotlib.use('Agg')  # Non-GUI backend
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(8, 5), dpi=80)
            ax.plot(
                self.x_data, 
                self.y_data, 
                'b-o', 
                linewidth=2, 
                markersize=6, 
                label='y = x²'
            )
            ax.set_title('Graph: y = x²')
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.grid(True, alpha=0.3)
            ax.legend()
            fig.tight_layout()
            
            # Save to PNG buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white')
            plt.close(fig)
            buf.seek(0)
            png_data = buf.read()
            
            # Convert to sixel
            if HAS_PIL:
                # Use our custom sixel converter (no external sixel libs!)
                sixel_data = SixelConverter.png_bytes_to_sixel(png_data)
                
                with open(output_path, 'w') as f:
                    f.write(sixel_data)
                
                self.call_from_thread(
                    self._update_status,
                    f"✓ Sixel saved: {output_path}"
                )
                self.call_from_thread(
                    self.notify,
                    f"Sixel plot saved!\n\n"
                    f"View command:\n"
                    f"  cat {output_path}\n\n"
                    f"Sixel-capable terminals:\n"
                    f"• xterm -ti vt340\n"
                    f"• mlterm\n"
                    f"• mintty\n"
                    f"• WezTerm",
                    title="Sixel Generated",
                    timeout=10
                )
            else:
                # Fallback: try external img2sixel command
                self._try_img2sixel_fallback(png_data, output_path)
                
        except Exception as e:
            self.call_from_thread(
                self.notify, 
                f"Sixel generation error: {e}", 
                severity="error"
            )
            self.call_from_thread(
                self._update_status, 
                f"✗ Sixel error: {e}"
            )
    
    def _try_img2sixel_fallback(self, png_data: bytes, output_path: str) -> None:
        """Fallback using external img2sixel command."""
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                f.write(png_data)
                temp_png = f.name
            
            result = subprocess.run(
                ['img2sixel', '-w', '600', temp_png],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_png)
            
            if result.returncode == 0:
                with open(output_path, 'w') as f:
                    f.write(result.stdout)
                
                self.call_from_thread(
                    self.notify,
                    f"Sixel saved (via img2sixel): {output_path}",
                    title="Success"
                )
            else:
                raise Exception("img2sixel command failed")
                
        except FileNotFoundError:
            self.call_from_thread(
                self.notify,
                "Neither PIL nor img2sixel available!\n\n"
                "Install PIL: pip install Pillow\n"
                "Or install libsixel: apt install libsixel-bin",
                severity="error",
                title="Missing Dependencies"
            )


# ============================================================================
# Entry Point
# ============================================================================

def main() -> None:
    """Entry point with feature detection output."""
    print("=" * 50)
    print("Graph Plotter - Textual Application")
    print("=" * 50)
    print("\nFeature Detection:")
    print(f"  ├─ PlotWidget: {'✓ Available' if HAS_PLOTWIDGET else '✗ pip install textual-plot'}")
    print(f"  ├─ Matplotlib: {'✓ Available' if HAS_MATPLOTLIB else '✗ pip install matplotlib'}")
    print(f"  └─ PIL/Pillow: {'✓ Available' if HAS_PIL else '✗ pip install Pillow'}")
    print("\nStarting application...\n")
    
    app = GraphPlotterApp()
    app.run()


if __name__ == "__main__":
    main()
