// ButlerCommand.cs
namespace ShieldShed.Models
{
    public class ButlerCommand
    {
        public string CommandText { get; set; }
        public CommandType Type { get; set; }
        public DateTime ExecutionTime { get; set; }
        public bool IsCompleted { get; set; }
    }

    public enum CommandType
    {
        Reminder,
        SmartHomeControl,
        InformationQuery,
        PasswordAction
    }
}

// FamilyMember.cs
namespace ShieldShed.Models
{
    public class FamilyMember
    {
        public string UserId { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public DateTime AddedDate { get; set; }
        public AccessLevel AccessLevel { get; set; }
    }

    public enum AccessLevel
    {
        ReadOnly,
        ReadWrite,
        Admin
    }
}