using System;
using System.Runtime.Serialization;

namespace NN_Studybuilder_Protocol.Exceptions
{
    public class LocalizationException : ApplicationException
    {
        public LocalizationException(string message) : base(message)
        {
        }

        public LocalizationException(string message, Exception innerException) : base(message, innerException)
        {
        }

        protected LocalizationException(SerializationInfo info, StreamingContext context) : base(info, context)
        {
        }
    }
}
