// PasswordEntry.cs
using System;

namespace ShieldShed.Models
{
    public class PasswordEntry
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public string ServiceName { get; set; } = string.Empty;
        public string Username { get; set; } = string.Empty;
        public string EncryptedPassword { get; set; } = string.Empty;
        public string WebsiteUrl { get; set; } = string.Empty;
        public string Notes { get; set; } = string.Empty;
        public DateTime CreatedDate { get; set; } = DateTime.UtcNow;
        public DateTime ModifiedDate { get; set; } = DateTime.UtcNow;
        public bool IsShared { get; set; }
        public List<string> SharedWithUserIds { get; set; } = new List<string>();
    }
}