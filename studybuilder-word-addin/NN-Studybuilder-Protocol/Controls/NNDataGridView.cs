using System.Drawing;
using System.Windows.Forms;

namespace NN_Studybuilder_Protocol.Controls
{
    // A DataGridView to show a configurable text when no results
    public class NNDataGridView : DataGridView
    {
        public string EmptyResultText { get; set; }

        public NNDataGridView()
        {
            Paint += NNDataGridView_Paint;
        }

        private void NNDataGridView_Paint(object sender, PaintEventArgs e)
        {
            if (!string.IsNullOrEmpty(EmptyResultText))
            {
                //if (Rows.Count == 0)
                //{
                //    using (var gfx = e.Graphics)
                //    {
                //        gfx.DrawString(EmptyResultText, Font, Brushes.Black,
                //            new PointF((Width - Font.Size * EmptyResultText.Length) / 2, Height / 2));
                //    }
                //}
                if (Rows.Count == 0)
                {
                    TextRenderer.DrawText(e.Graphics, EmptyResultText,
                        Font, ClientRectangle,
                        ForeColor, BackgroundColor,
                        TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
                }
            }
        }
    }
}
