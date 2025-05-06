using Microsoft.Office.Core;
using Microsoft.Office.Interop.Word;
using System;
using System.IO;
using System.Reflection;

namespace NN_Studybuilder_Protocol.Data.Services
{
    /// <summary>
    /// Insert files and images
    /// </summary>
    public class FileHandler
    {
        private readonly ContentControlManager contentControlManager;

        public FileHandler(ContentControlManager contentControlManager)
        {
            this.contentControlManager = contentControlManager;
        }

        public void SetTableStyle(Range range)
        {
            if (range == null) throw new ArgumentNullException(nameof(range));

            // We can't update the content control so we need to get it again
            var cc = contentControlManager.GetContentControlByTag(range.ParentContentControl.Tag);
            if (cc == null) throw new Exception($"Content control with tag {range.ParentContentControl.Tag} not found");

            // Set styling and header format on the newly inserted table
            var styleName = "SB Table Condensed";
            Table table = null;
            try
            {
                if (cc.Range.Tables.Count > 0)
                {
                    table = cc.Range.Tables[1];
                    table.set_Style(styleName);
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Could not apply table style with name {styleName}: {ex.Message}");
            }

            if (table == null) return;

            var numHeadings = 4;
            for (int i = 1; i <= numHeadings; i++)
            {
                table.Rows[i].HeadingFormat = (int)MsoTriState.msoTrue;
                table.Rows[i].AllowBreakAcrossPages = (int)MsoTriState.msoTrue;
            }
        }

        public void InsertFile(byte[] file, Range range, string filename)
        {
            if (range == null) throw new ArgumentNullException(nameof(range));

            var filePath = GetLocationPath(filename);

            // Save doc to local folder
            File.WriteAllBytes(filePath, file);

            // Remove existing tables
            for (int i = 1; i <= range.Tables.Count; i++)
            {
                range.Tables[i].Delete();
            }

            range.InsertFile(filePath);

            File.Delete(filePath);
        }

        public void InsertImage(byte[] image, Range range, string filename)
        {
            if (range == null) throw new ArgumentNullException(nameof(range));

            var filePath = GetLocationPath(filename);
            // Save image to local folder
            File.WriteAllBytes(filePath, image);

            range.InlineShapes.AddPicture(filePath);
            if (range.InlineShapes.Count > 1)
            {
                range.InlineShapes[1].Delete();
            }

            File.Delete(filePath);
        }

        protected virtual string GetLocationPath(string filename)
        {
            // Get the user's profile folder path
            var userProfilePath = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            return Path.Combine(userProfilePath, filename);
        }
    }
}
