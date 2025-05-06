using NN_Studybuilder_Protocol.Exceptions;

namespace NN_Studybuilder_Protocol.Controls
{
    internal static class LocalizationManager
    {
        internal static string GetLabel(string controlId)
        {
            var tes = Properties.Resources.ResourceManager.GetString(controlId + "_Label");
            if (string.IsNullOrWhiteSpace(tes))
            {
                throw new LocalizationException($"Control with id {controlId} not found");
            }

            return tes;
        }

        internal static string GetScreentip(string controlId)
        {
            var tes = Properties.Resources.ResourceManager.GetString(controlId + "_Screentip");
            if (string.IsNullOrWhiteSpace(tes))
            {
                throw new LocalizationException($"Control with id {controlId} not found");
            }

            return tes;
        }

        internal static string GetSupertip(string controlId)
        {
            var tes = Properties.Resources.ResourceManager.GetString(controlId + "_Supertip");
            if (string.IsNullOrWhiteSpace(tes))
            {
                throw new LocalizationException($"Control with id {controlId} not found");
            }

            return tes;
        }
    }
}
