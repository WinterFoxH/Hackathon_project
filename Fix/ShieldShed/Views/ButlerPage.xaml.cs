using ShieldShed.ViewModels;
using Microsoft.Maui.Controls;

namespace ShieldShed
{
    public partial class ButlerPage : ContentPage
    {
        public ButlerPage(ButlerViewModel viewModel)
        {
            InitializeComponent();
            BindingContext = viewModel;
        }
    }
}