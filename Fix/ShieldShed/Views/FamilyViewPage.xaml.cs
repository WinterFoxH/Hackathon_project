using ShieldShed.ViewModels;
using Microsoft.Maui.Controls;

namespace ShieldShed
{
    public partial class FamilyPage : ContentPage
    {
        public FamilyPage(FamilyViewModel viewModel)
        {
            InitializeComponent();
            BindingContext = viewModel;
        }
    }
}