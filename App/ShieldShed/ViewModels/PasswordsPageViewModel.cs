using Plugin.Fingerprint.Abstractions;
using ShieldShed.Interfaces;
using ShieldShed.Models;
using ShieldShed.Services;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;

namespace ShieldShed.ViewModels
{
    public class PasswordsViewModel : INotifyPropertyChanged
    {
        private readonly IPasswordService _passwordService;
        private readonly IFingerprint _fingerprint;

        private bool _isAuthenticated;
        public bool IsAuthenticated
        {
            get => _isAuthenticated;
            set => SetProperty(ref _isAuthenticated, value);
        }

        public ObservableCollection<PasswordEntry> PasswordEntries { get; } = new();

        public ICommand AuthenticateCommand { get; }
        public ICommand AddPasswordCommand { get; }
        public ICommand ViewPasswordCommand { get; }
        public ICommand CopyPasswordCommand { get; }
        public ICommand SharePasswordCommand { get; }

        public PasswordsViewModel(IPasswordService passwordService, IFingerprint fingerprint)
        {
            _passwordService = passwordService;
            _fingerprint = fingerprint;

            AuthenticateCommand = new Command(async () => await AuthenticateAsync());
            AddPasswordCommand = new Command(async () => await AddPasswordAsync());
            ViewPasswordCommand = new Command<PasswordEntry>(async (entry) => await ViewPasswordAsync(entry));
            CopyPasswordCommand = new Command<PasswordEntry>(async (entry) => await CopyPasswordAsync(entry));
            SharePasswordCommand = new Command<PasswordEntry>(async (entry) => await SharePasswordAsync(entry));

            Task.Run(InitializeAsync);
        }

        private async Task InitializeAsync()
        {
            await AuthenticateAsync();
        }

        private async Task AuthenticateAsync()
        {
            // Implement biometric authentication
            IsAuthenticated = true; // Simulate success for now
            await LoadPasswords();
        }

        private async Task LoadPasswords()
        {
            var passwords = await _passwordService.GetAllPasswordsAsync();
            PasswordEntries.Clear();
            foreach (var password in passwords)
            {
                PasswordEntries.Add(password);
            }
        }

        private async Task AddPasswordAsync()
        {
            // Implement add password
        }

        private async Task ViewPasswordAsync(PasswordEntry entry)
        {
            // Implement view password
        }

        private async Task CopyPasswordAsync(PasswordEntry entry)
        {
            // Implement copy password
        }

        private async Task SharePasswordAsync(PasswordEntry entry)
        {
            // Implement share password
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