using ShieldShed.ViewModels;
using Microsoft.Maui.Controls;

namespace ShieldShed
{
    public partial class PasswordsPage : ContentPage
    {
        public PasswordsPage(PasswordsViewModel viewModel)
        {
            InitializeComponent();
            BindingContext = viewModel;
        }
    }
}