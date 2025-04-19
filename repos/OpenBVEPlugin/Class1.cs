using System;
using System.Xml.Linq;
using OpenBveApi.Runtime;
using System.Runtime.InteropServices;
using System.Collections.Generic;

namespace Plugin
{

    public static class ConsoleManager
    {
        [DllImport("kernel32.dll")]
        private static extern bool AllocConsole();

        [DllImport("kernel32.dll")]
        private static extern bool FreeConsole();

        public static void Show()
        {
            AllocConsole();
        }

        public static void Hide()
        {
            FreeConsole();
        }
    }

    /// <summary>The interface to be implemented by the plugin.</summary>
    public partial class Plugin : IRuntime
    {

        /// <summary>Holds the array of panel variables.</summary>
        /// <remarks>Be sure to initialize in the Load call.</remarks>
        private int[] Panel = null;

        /// <summary>Holds the aspect last reported to the plugin in the SetSignal call.</summary>
        private int LastAspect = -1;

        /// <summary>Is called when the plugin is loaded.</summary>
        /// <param name="properties">The properties supplied to the plugin on loading.</param>
        /// <returns>Whether the plugin was loaded successfully.</returns>
        public bool Load(LoadProperties properties)
        {
            ConsoleManager.Show();  // 콘솔 창 열기

            Panel = new int[256];
            Sound = new SoundHelper(properties.PlaySound, 256);
            properties.Panel = Panel;
            properties.AISupport = AISupport.None;

            Console.WriteLine("🚀 Plugin loaded!");

            return true;
        }

        /// <summary>Is called when the plugin is unloaded.</summary>
        public void Unload()
        {
            // TODO: Your old Dispose code goes here.
        }

        /// <summary>Is called after loading to inform the plugin about the specifications of the train.</summary>
        /// <param name="specs">The specifications of the train.</param>
        public void SetVehicleSpecs(VehicleSpecs specs)
        {
            // TODO: Your old SetVehicleSpec code goes here.
        }

        /// <summary>Is called when the plugin should initialize or reinitialize.</summary>
        /// <param name="mode">The mode of initialization.</param>
        public void Initialize(InitializationModes mode)
        {
            // TODO: Your old Initialize code goes here.
        }

        /// <summary>Is called every frame.</summary>
        /// <param name="data">The data passed to the plugin.</param>
        public void Elapse(ElapseData data)
        {
            double location = data.Vehicle.Location; // 위치 (미터)
            double speed = data.Vehicle.Speed.KilometersPerHour; // 속도 (km/h)
            List<double> World = data.Vehicle.Worlds;

            Console.WriteLine($"위치: {location:F2} m / 속도: {speed:F1} km/h / 좌표: X={World[0]:F4}, Y={World[1]:F4}, Z={World[2]:F2}");

            Sound.Update();
        }



        /// <summary>Is called when the driver changes the reverser.</summary>
        /// <param name="reverser">The new reverser position.</param>
        public void SetReverser(int reverser)
        {
            // TODO: Your old SetReverser code goes here.
        }

        /// <summary>Is called when the driver changes the power notch.</summary>
        /// <param name="powerNotch">The new power notch.</param>
        public void SetPower(int powerNotch)
        {
            // TODO: Your old SetPower code goes here.
        }

        /// <summary>Is called when the driver changes the brake notch.</summary>
        /// <param name="brakeNotch">The new brake notch.</param>
        public void SetBrake(int brakeNotch)
        {
            // TODO: Your old SetBrake code goes here.
        }

        /// <summary>Is called when a virtual key is pressed.</summary>
        /// <param name="key">The virtual key that was pressed.</param>
        public void KeyDown(VirtualKeys key)
        {
            // TODO: Your old KeyDown code goes here.
        }

        /// <summary>Is called when a virtual key is released.</summary>
        /// <param name="key">The virtual key that was released.</param>
        public void KeyUp(VirtualKeys key)
        {
            // TODO: Your old KeyUp code goes here.
        }

        /// <summary>Is called when a horn is played or when the music horn is stopped.</summary>
        /// <param name="type">The type of horn.</param>
        public void HornBlow(HornTypes type)
        {
            // TODO: Your old HornBlow code goes here.
        }

        /// <summary>Is called when the state of the doors changes.</summary>
        /// <param name="oldState">The old state of the doors.</param>
        /// <param name="newState">The new state of the doors.</param>
        public void DoorChange(DoorStates oldState, DoorStates newState)
        {
            if (oldState == DoorStates.None & newState != DoorStates.None)
            {
                // TODO: Your old DoorOpen code goes here.
            }
            else if (oldState != DoorStates.None & newState == DoorStates.None)
            {
                // TODO: Your old DoorClose code goes here.
            }
        }

        /// <summary>Is called when the aspect in the current or in any of the upcoming sections changes, or when passing section boundaries.</summary>
        /// <param name="data">Signal information per section. In the array, index 0 is the current section, index 1 the upcoming section, and so on.</param>
        /// <remarks>The signal array is guaranteed to have at least one element. When accessing elements other than index 0, you must check the bounds of the array first.</remarks>
        public void SetSignal(SignalData[] signal)
        {
            int aspect = signal[0].Aspect;
            if (aspect != this.LastAspect)
            {
                // TODO: Your old SetSignal code goes here.
            }
        }

        /// <summary>Is called when the train passes a beacon.</summary>
        /// <param name="beacon">The beacon data.</param>
        public void SetBeacon(BeaconData beacon)
        {
            // TODO: Your old SetBeaconData code goes here.
        }

        /// <summary>Is called when the plugin should perform the AI.</summary>
        /// <param name="data">The AI data.</param>
        public void PerformAI(AIData data)
        {
            // TODO: Implement this function if you want your plugin to support the AI.
            //       Be to set properties.AISupport to AISupport.Basic in the Load call if you do.
        }

        public void Getcoordinates()
        {
            Console.WriteLine("현재속도");
        }

    }
}