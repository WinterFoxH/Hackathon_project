using ShieldShed.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ShieldShed.Interfaces
{
    public interface IPasswordService
    {
        Task<List<PasswordEntry>> GetAllPasswordsAsync();
        Task<PasswordEntry> GetPasswordByIdAsync(Guid id);
        Task AddOrUpdatePasswordAsync(PasswordEntry entry);
        Task DeletePasswordAsync(Guid id);
        Task<string> DecryptPasswordAsync(string encryptedPassword);
        Task<string> EncryptPasswordAsync(string plainTextPassword);
        Task SharePasswordAsync(Guid passwordId, string userId, AccessLevel accessLevel);
    }
}
