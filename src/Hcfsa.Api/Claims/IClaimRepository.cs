namespace Hcfsa.Api.Claims;

public interface IClaimRepository
{
    ClaimResponse? GetClaim(Guid claimId);
    void SaveClaim(ClaimResponse claim);
    void UpdateClaim(ClaimResponse claim);
    void AddExpense(Guid claimId, ClaimExpenseResponse expense);
    void AttachDocument(Guid claimId, Guid expenseId, ClaimDocumentResponse document);
    void AddAuditEvent(AuditEvent auditEvent);
    IReadOnlyList<AuditEvent> GetAuditEvents(string entityType, Guid entityId);
}

public sealed class InMemoryClaimRepository : IClaimRepository
{
    private readonly object _lock = new();
    private readonly Dictionary<Guid, ClaimResponse> _claims = [];
    private readonly List<AuditEvent> _auditEvents = [];

    public ClaimResponse? GetClaim(Guid claimId)
    {
        lock (_lock) return _claims.GetValueOrDefault(claimId);
    }

    public void SaveClaim(ClaimResponse claim)
    {
        lock (_lock) _claims.Add(claim.Id, claim);
    }

    public void UpdateClaim(ClaimResponse claim)
    {
        lock (_lock) _claims[claim.Id] = claim;
    }

    public void AddExpense(Guid claimId, ClaimExpenseResponse expense)
    {
        lock (_lock)
        {
            var claim = _claims[claimId];
            _claims[claimId] = claim with { Expenses = [..claim.Expenses, expense] };
        }
    }

    public void AttachDocument(Guid claimId, Guid expenseId, ClaimDocumentResponse document)
    {
        lock (_lock)
        {
            var claim = _claims[claimId];
            var expenses = claim.Expenses
                .Select(expense => expense.Id == expenseId ? expense with { Documents = [..expense.Documents, document] } : expense)
                .ToArray();
            _claims[claimId] = claim with { Expenses = expenses };
        }
    }

    public void AddAuditEvent(AuditEvent auditEvent)
    {
        lock (_lock) _auditEvents.Add(auditEvent);
    }

    public IReadOnlyList<AuditEvent> GetAuditEvents(string entityType, Guid entityId)
    {
        lock (_lock)
        {
            return _auditEvents
                .Where(auditEvent => auditEvent.EntityType == entityType && auditEvent.EntityId == entityId)
                .OrderBy(auditEvent => auditEvent.OccurredAt)
                .ToArray();
        }
    }
}
