using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol.Controls
{
    public class CustomProgressBar : ProgressBar
    {
        public CustomProgressBar()
        {
            SetStyle(ControlStyles.UserPaint, true);
        }

        protected override void OnPaintBackground(PaintEventArgs pevent) 
        {
            // Prevent control flicker
            base.OnPaintBackground(pevent);
        }                  

        protected override void OnPaint(PaintEventArgs e)
        {
            // Size of the inner rectangle
            const int inset = 2; 

            using (Image offscreenImage = new Bitmap(Width, Height))
            {
                using (Graphics offscreen = Graphics.FromImage(offscreenImage))
                {
                    Rectangle rect = new Rectangle(0, 0, Width, Height);

                    if (ProgressBarRenderer.IsSupported)
                        ProgressBarRenderer.DrawHorizontalBar(offscreen, rect);

                    // Deflate inner rectangle
                    rect.Inflate(new Size(-inset, -inset)); 
                    rect.Width = (int)(rect.Width * ((double)Value / Maximum));

                    if (rect.Width != 0)
                    {
                        var brush = new LinearGradientBrush(rect, Color.Green, Color.White, LinearGradientMode.Vertical);
                        offscreen.FillRectangle(brush, inset, inset, rect.Width, rect.Height);
                        e.Graphics.DrawImage(offscreenImage, 0, 0);
                    }
                }
            }
        }
    }
}
