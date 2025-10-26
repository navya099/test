using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Autodesk.AutoCAD.Runtime;
using Autodesk.AutoCAD.EditorInput;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Geometry;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using CoreApp = Autodesk.AutoCAD.ApplicationServices.Core.Application;
using Autodesk.AutoCAD.ApplicationServices;
namespace ClassLibrary1
{
    public class C3D_Plugin : IExtensionApplication
    {
        public void Initialize()
        {
            Application.DocumentManager.MdiActiveDocument.Editor.WriteMessage("\n[C3D Exporter] 플러그인 초기화 완료.");
        }

        public void Terminate() { }

        [CommandMethod("ExtractALLAlignmentoffset")]
        public void ExtractALLAlignmentoffset()
        {
            try
            {
                var processor = new AlignmentProcessor();
                processor.ExportAllOffsets();
            }
            catch (Autodesk.AutoCAD.Runtime.Exception ex)
            {
                Application.DocumentManager.MdiActiveDocument.Editor.WriteMessage($"\n[ERROR] 실행 실패: {ex.Message}");
            }
        }
    }
}