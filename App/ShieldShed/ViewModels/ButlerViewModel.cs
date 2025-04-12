using ShieldShed.Interfaces;
using ShieldShed.Models;
using ShieldShed.Services;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;

namespace ShieldShed.ViewModels
{
    public class ButlerViewModel : INotifyPropertyChanged
    {
        private readonly IButlerService _butlerService;

        public ObservableCollection<ButlerCommand> RecentCommands { get; } = new();
        public ICommand StartListeningCommand { get; }

        private string _statusMessage = "Ready";
        public string StatusMessage
        {
            get => _statusMessage;
            set => SetProperty(ref _statusMessage, value);
        }

        public ButlerViewModel(IButlerService butlerService)
        {
            _butlerService = butlerService;
            StartListeningCommand = new Command(async () => await StartListeningAsync());

            LoadRecentCommands();
        }

        private async Task StartListeningAsync()
        {
            StatusMessage = "Listening...";
            await Task.Delay(1000); // Simulate listening
            StatusMessage = "Processing command...";

            // Process the command
            await _butlerService.ProcessVoiceCommandAsync("sample command");

            // Reload commands
            await LoadRecentCommands();

            StatusMessage = "Ready";
        }

        private async Task LoadRecentCommands()
        {
            var commands = await _butlerService.GetPendingCommandsAsync();
            RecentCommands.Clear();
            foreach (var cmd in commands)
            {
                RecentCommands.Add(cmd);
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;

        protected void OnPropertyChanged([CallerMemberName] string propertyName = "")
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        protected bool SetProperty<T>(ref T backingStore, T value, [CallerMemberName] string propertyName = "")
        {
            if (EqualityComparer<T>.Default.Equals(backingStore, value))
                return false;

            backingStore = value;
            OnPropertyChanged(propertyName);
            return true;
        }
    }
}