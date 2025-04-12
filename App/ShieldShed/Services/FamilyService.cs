using ShieldShed.Interfaces;
using ShieldShed.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ShieldShed.Services
{
    public class FamilyService : IFamilyService
    {
        public Task AddFamilyMemberAsync(string email, string name, AccessLevel accessLevel)
        {
            throw new NotImplementedException();
        }

        public Task RemoveFamilyMemberAsync(string userId)
        {
            throw new NotImplementedException();
        }

        public Task<List<FamilyMember>> GetFamilyMembersAsync()
        {
            // Return sample data for now
            return Task.FromResult(new List<FamilyMember>
            {
                new FamilyMember { Name = "Family Member 1", Email = "member1@example.com" }
            });
        }

        public Task UpdateAccessLevelAsync(string userId, AccessLevel newLevel)
        {
            throw new NotImplementedException();
        }
    }
}