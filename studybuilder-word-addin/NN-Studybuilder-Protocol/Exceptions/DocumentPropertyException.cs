using System;

namespace NN_Studybuilder_Protocol.Exceptions
{
    public class DocumentPropertyException : Exception
    {
        public string Key { get; set; }
    }
}
