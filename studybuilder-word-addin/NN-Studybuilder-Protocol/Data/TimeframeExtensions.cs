namespace NN_Studybuilder_Protocol.Data
{
    public static class TimeframeExtensions
    {
        public static string Format(this TimeframeDto obj)
        {
            if (obj == null) return string.Empty;
            return obj.Name;
        }
    }
}
