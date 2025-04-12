using ShieldShed.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ShieldShed.Interfaces
{
    public interface IButlerService
    {
        Task ProcessVoiceCommandAsync(string command);
        Task AddReminderAsync(string reminderText, DateTime reminderTime);
        Task<List<ButlerCommand>> GetPendingCommandsAsync();
        Task CompleteCommandAsync(string commandId);
    }
}