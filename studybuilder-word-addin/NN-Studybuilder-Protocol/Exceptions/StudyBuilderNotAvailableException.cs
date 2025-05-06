using System;
using System.Runtime.Serialization;

namespace NN_Studybuilder_Protocol.Exceptions
{
    public class StudyBuilderNotAvailableException : Exception
    {
        public StudyBuilderNotAvailableException()
        {
        }

        public StudyBuilderNotAvailableException(string message) : base(message)
        {
        }

        public StudyBuilderNotAvailableException(string message, Exception innerException) : base(message, innerException)
        {
        }

        protected StudyBuilderNotAvailableException(SerializationInfo info, StreamingContext context) : base(info, context)
        {
        }
    }
}
