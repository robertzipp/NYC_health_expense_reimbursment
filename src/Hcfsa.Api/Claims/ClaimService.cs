namespace Hcfsa.Api.Claims;

public sealed class ClaimService(IClaimRepository repository)
{
    public ClaimResponse CreateClaim(ActorContext actor, CreateClaimRequest request)
    {
        if (actor.ActorType == "employee" && actor.ActorId != request.EmployeeId)
        {
            throw new UnauthorizedAccessException("Employees may only create their own claims.");
        }

        var claim = new ClaimResponse(Guid.NewGuid(), actor.AgencyId, request.EmployeeId, ClaimStatus.Draft, DateTimeOffset.UtcNow, null, []);
        repository.SaveClaim(claim);
        Audit(actor, "claim.created", "success", claim.Id, new Dictionary<string, object?> { ["employee_id"] = request.EmployeeId });
        return claim;
    }

    public ClaimResponse? GetClaim(ActorContext actor, Guid claimId)
    {
        var claim = repository.GetClaim(claimId);
        return claim is not null && CanAccess(actor, claim) ? claim : null;
    }

    public ClaimExpenseResponse AddExpense(ActorContext actor, Guid claimId, AddExpenseRequest request)
    {
        var claim = RequireAccessibleDraft(actor, claimId);
        var serviceValidation = ClaimApiValidation.ValidateExpense(request);
        if (serviceValidation.Count > 0) throw new ArgumentException(serviceValidation[0].Issue);

        var expense = new ClaimExpenseResponse(
            Guid.NewGuid(),
            request.Claimant.Trim(),
            request.DateOfService,
            request.ExpenseCategory.Trim(),
            request.AmountCharged,
            request.RequestedReimbursementAmount,
            request.ServiceType.Trim(),
            request.DocumentationRequired ?? true,
            []);

        repository.AddExpense(claim.Id, expense);
        Audit(actor, "claim_expense.added", "success", claim.Id, new Dictionary<string, object?> { ["expense_id"] = expense.Id });
        return expense;
    }

    public ClaimDocumentResponse AttachDocument(ActorContext actor, Guid claimId, Guid expenseId, AttachDocumentRequest request)
    {
        var claim = RequireAccessibleDraft(actor, claimId);
        if (claim.Expenses.All(expense => expense.Id != expenseId)) throw new KeyNotFoundException("Expense was not found on this claim.");

        var serviceValidation = ClaimApiValidation.ValidateDocument(request);
        if (serviceValidation.Count > 0) throw new ArgumentException(serviceValidation[0].Issue);

        // Only metadata is persisted; document binaries stay in object storage managed by the upload pipeline.
        var document = new ClaimDocumentResponse(
            Guid.NewGuid(),
            expenseId,
            Path.GetFileName(request.FileName.Trim()),
            request.MimeType.Trim().ToLowerInvariant(),
            request.SizeBytes,
            request.ChecksumSha256.Trim().ToLowerInvariant(),
            request.DocumentType.Trim(),
            DateTimeOffset.UtcNow);

        repository.AttachDocument(claim.Id, expenseId, document);
        Audit(actor, "claim_document.attached", "success", claim.Id, new Dictionary<string, object?> { ["expense_id"] = expenseId, ["document_id"] = document.Id });
        return document;
    }

    public ClaimValidationResult ValidateClaim(ActorContext actor, Guid claimId)
    {
        var claim = RequireAccessible(actor, claimId);
        var details = ValidateForSubmission(claim);
        return new ClaimValidationResult(details.Count == 0, details);
    }

    public ClaimValidationResult SubmitClaim(ActorContext actor, Guid claimId)
    {
        var claim = RequireAccessible(actor, claimId);
        if (claim.Status != ClaimStatus.Draft) throw new InvalidOperationException("Claim cannot be submitted twice.");

        var details = ValidateForSubmission(claim);
        if (details.Count > 0)
        {
            Audit(actor, "claim.validation_failed", "failure", claim.Id, new Dictionary<string, object?> { ["details"] = details });
            return new ClaimValidationResult(false, details);
        }

        var submitted = claim with { Status = ClaimStatus.Submitted, SubmittedAt = DateTimeOffset.UtcNow };
        repository.UpdateClaim(submitted);
        Audit(actor, "claim.submitted", "success", claim.Id, new Dictionary<string, object?> { ["submitted_at"] = submitted.SubmittedAt });
        return new ClaimValidationResult(true, [], submitted);
    }

    public IReadOnlyList<AuditEvent> AuditEventsForClaim(ActorContext actor, Guid claimId)
    {
        var claim = RequireAccessible(actor, claimId);
        return repository.GetAuditEvents("claim", claim.Id);
    }

    private ClaimResponse RequireAccessibleDraft(ActorContext actor, Guid claimId)
    {
        var claim = RequireAccessible(actor, claimId);
        if (claim.Status != ClaimStatus.Draft) throw new InvalidOperationException("A non-draft claim cannot be edited by the employee.");
        return claim;
    }

    private ClaimResponse RequireAccessible(ActorContext actor, Guid claimId)
    {
        var claim = repository.GetClaim(claimId) ?? throw new KeyNotFoundException("Claim was not found.");
        if (!CanAccess(actor, claim)) throw new UnauthorizedAccessException("Actor cannot access this claim.");
        return claim;
    }

    private static bool CanAccess(ActorContext actor, ClaimResponse claim) =>
        actor.AgencyId == claim.AgencyId && (actor.ActorType != "employee" || actor.ActorId == claim.EmployeeId);

    private static List<ValidationDetail> ValidateForSubmission(ClaimResponse claim)
    {
        var details = new List<ValidationDetail>();
        if (claim.Expenses.Count == 0) details.Add(new("expenses", "submitted claim must have at least one expense"));

        foreach (var expense in claim.Expenses)
        {
            details.AddRange(ClaimApiValidation.ValidateExpense(new AddExpenseRequest(expense.Claimant, expense.DateOfService, expense.ExpenseCategory, expense.AmountCharged, expense.RequestedReimbursementAmount, expense.ServiceType, expense.DocumentationRequired)));
            if (expense.DocumentationRequired && expense.Documents.Count == 0)
            {
                details.Add(new($"expenses[{expense.Id}].documents", "supporting document is required for this expense"));
            }
        }

        return details;
    }

    private void Audit(ActorContext actor, string eventType, string outcome, Guid claimId, IReadOnlyDictionary<string, object?> data)
    {
        repository.AddAuditEvent(new AuditEvent(Guid.NewGuid(), eventType, outcome, "claim", claimId, actor.ActorType, actor.ActorId, actor.AgencyId, actor.CorrelationId, DateTimeOffset.UtcNow, data));
    }
}
