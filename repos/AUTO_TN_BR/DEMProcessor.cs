using System;
using System.Diagnostics;

namespace AUTO_TN_BR
{
    public class DEMProcessor
    {
        private readonly string pythonExe = @"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe";
        private readonly string scriptPath = @"C:\Users\Administrator\Documents\파이썬\strm30_표고가져오기_civil3d_net용.py";

        public bool RunPythonScript()
        {
            try
            {
                var psi = new ProcessStartInfo
                {
                    FileName = pythonExe,
                    Arguments = $"\"{scriptPath}\"",   // 실행할 스크립트 지정 (★ 빠져 있었음)
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,      // 오류 메시지도 캡처
                    UseShellExecute = false,
                    CreateNoWindow = true
                };

                using var proc = Process.Start(psi);

                // 출력 읽기
                string output = proc.StandardOutput.ReadToEnd();
                string error = proc.StandardError.ReadToEnd();
                proc.WaitForExit();

                Console.WriteLine("Python Output:");
                Console.WriteLine(output);

                if (!string.IsNullOrEmpty(error))
                {
                    Console.WriteLine("Python Error:");
                    Console.WriteLine(error);
                }

                return proc.ExitCode == 0;  // 0이면 정상 종료
            }
            catch (Exception ex)
            {
                Console.WriteLine("Python 실행 중 예외 발생: " + ex.Message);
                return false;
            }
        }
    }
}
