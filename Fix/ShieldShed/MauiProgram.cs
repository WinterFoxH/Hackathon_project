// MauiProgram.cs
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Plugin.Fingerprint;
using Plugin.Fingerprint.Abstractions;
using ShieldShed.Interfaces;
using ShieldShed.Services;
using ShieldShed.ViewModels;

namespace ShieldShed
{
    public static class MauiProgram
    {
        public static MauiApp CreateMauiApp()
        {
            var builder = MauiApp.CreateBuilder();
            builder
                .UseMauiApp<App>()
                .ConfigureFonts(fonts =>
                {
                    fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
                    fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
                });

#if DEBUG
            builder.Logging.AddDebug();
#endif

            // Services
            builder.Services.AddSingleton<IFingerprint>(CrossFingerprint.Current);
            builder.Services.AddSingleton<IPasswordService, PasswordService>();
            builder.Services.AddSingleton<IButlerService, ButlerService>();
            builder.Services.AddSingleton<IFamilyService, FamilyService>();

            // ViewModels
            builder.Services.AddTransient<PasswordsViewModel>();
            builder.Services.AddTransient<ButlerViewModel>();
            builder.Services.AddTransient<FamilyViewModel>();

            // Views
            builder.Services.AddTransient<PasswordsPage>();
            builder.Services.AddTransient<ButlerPage>();
            builder.Services.AddTransient<FamilyPage>();

            return builder.Build();
        }
    }
}