using ShieldShed.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ShieldShed.Interfaces
{
    public interface IFamilyService
    {
        Task AddFamilyMemberAsync(string email, string name, AccessLevel accessLevel);
        Task RemoveFamilyMemberAsync(string userId);
        Task<List<FamilyMember>> GetFamilyMembersAsync();
        Task UpdateAccessLevelAsync(string userId, AccessLevel newLevel);
    }
}