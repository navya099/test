using Autodesk.AutoCAD.EditorInput;
using System;
using System.Collections.Generic;
using System.IO;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;

namespace AUTO_TN_BR
{
    internal sealed class Logger
    {
        private static readonly Lazy<Logger> _instance = new Lazy<Logger>(() => new Logger());
        public static Logger Instance => _instance.Value;

        public string LastMessage { get; private set; }
        public List<string> LogMessages { get; private set; }
        public Editor Editor { get; private set; }

        private Logger()
        {
            try
            {
                Editor = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            }
            catch
            {
                Editor = null;
            }

            LogMessages = new List<string>();
        }

        public void SetMessage(string msg)
        {
            string timestampedMsg = $"[{DateTime.Now:HH:mm:ss}] {msg}";
            LastMessage = timestampedMsg;
            LogMessages.Add(timestampedMsg);
            Editor = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            Editor?.WriteMessage("\n" + timestampedMsg);
        }

        public void SaveLogToTXT(string logFilePath = @"C:\temp\AUTODEM_Log.txt")
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(logFilePath));
                File.WriteAllLines(logFilePath, LogMessages);
                SetMessage($"로그 파일 저장 완료: {logFilePath}");
            }
            catch (Exception ex)
            {
                SetMessage($"로그 저장 실패: {ex.Message}");
            }
        }

        public void ClearLog()
        {
            LogMessages.Clear();
            LastMessage = string.Empty;
        }

        public void ResetEditor()
        {
            try
            {
                Editor = CoreApp.DocumentManager.MdiActiveDocument.Editor;
            }
            catch
            {
                Editor = null;
            }
        }
    }
}
