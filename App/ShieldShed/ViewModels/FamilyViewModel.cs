using ShieldShed.Interfaces;
using ShieldShed.Models;
using ShieldShed.Services;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;

namespace ShieldShed.ViewModels
{
    public class FamilyViewModel : INotifyPropertyChanged
    {
        private readonly IFamilyService _familyService;

        public ObservableCollection<FamilyMember> FamilyMembers { get; } = new();
        public ICommand AddMemberCommand { get; }

        public FamilyViewModel(IFamilyService familyService)
        {
            _familyService = familyService;
            AddMemberCommand = new Command(async () => await AddMemberAsync());

            LoadFamilyMembers();
        }

        private async Task LoadFamilyMembers()
        {
            var members = await _familyService.GetFamilyMembersAsync();
            FamilyMembers.Clear();
            foreach (var member in members)
            {
                FamilyMembers.Add(member);
            }
        }

        private async Task AddMemberAsync()
        {
            // Implement add member functionality
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