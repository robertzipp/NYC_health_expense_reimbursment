namespace Hcfsa.Api.Claims;

public sealed class ClaimService(IClaimRepository repository)
{
    public ClaimResponse CreateClaim(ActorContext actor, CreateClaimRequest request)
    {
        if (string.IsNullOrWhiteSpace(request.EmployeeId)) throw new ArgumentException("employee_id is required");
        if (actor.ActorType == "employee" && actor.ActorId != request.EmployeeId) throw new UnauthorizedAccessException("Employee can only create their own claim.");

        var claim = new ClaimResponse(Guid.NewGuid(), actor.AgencyId, request.EmployeeId.Trim(), ClaimStatus.Draft, DateTimeOffset.UtcNow, null, []);
        repository.SaveClaim(claim);
        Audit(actor, "claim.created", "success", "claim", claim.Id, new Dictionary<string, object?> { ["employee_id"] = request.EmployeeId });
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
        Audit(actor, "claim_expense.added", "success", "claim", claim.Id, new Dictionary<string, object?> { ["expense_id"] = expense.Id });
        return expense;
    }

    public ClaimDocumentResponse AttachDocument(ActorContext actor, Guid claimId, Guid expenseId, AttachDocumentRequest request)
    {
        var claim = RequireAccessibleDraft(actor, claimId);
        if (claim.Expenses.All(expense => expense.Id != expenseId)) throw new KeyNotFoundException("Expense was not found on this claim.");

        var serviceValidation = ClaimApiValidation.ValidateDocument(request);
        if (serviceValidation.Count > 0) throw new ArgumentException(serviceValidation[0].Issue);

        var document = CreateDocument(expenseId, null, request);
        repository.AttachDocument(claim.Id, expenseId, document);
        Audit(actor, "claim_document.attached", "success", "claim", claim.Id, new Dictionary<string, object?> { ["expense_id"] = expenseId, ["document_id"] = document.Id });
        return document;
    }

    public ReceiptResponse CreateReceipt(ActorContext actor, CreateReceiptRequest request)
    {
        var documentRequest = new AttachDocumentRequest(request.FileName, request.MimeType, request.SizeBytes, request.ChecksumSha256, request.DocumentType);
        var validation = ClaimApiValidation.ValidateDocument(documentRequest);
        if (validation.Count > 0) throw new ArgumentException(validation[0].Issue);

        var timestamp = DateTimeOffset.UtcNow;
        var receipt = new ReceiptResponse(
            Guid.NewGuid(), actor.AgencyId, actor.ActorId, Path.GetFileName(request.FileName.Trim()), request.MimeType.Trim().ToLowerInvariant(), request.SizeBytes,
            request.ChecksumSha256.Trim().ToLowerInvariant(), request.DocumentType.Trim(), string.IsNullOrWhiteSpace(request.Description) ? null : request.Description.Trim(),
            ReceiptStatus.Available, null, null, timestamp, timestamp, null, null);

        repository.SaveReceipt(receipt);
        Audit(actor, "receipt.created", "success", "receipt", receipt.Id, new Dictionary<string, object?> { ["file_name"] = receipt.FileName });
        return receipt;
    }

    public IReadOnlyList<ReceiptResponse> ListReceipts(ActorContext actor, bool includeArchived = false) =>
        repository.ListReceipts(actor.AgencyId, actor.ActorId, includeArchived);

    public ReceiptResponse UpdateReceipt(ActorContext actor, Guid receiptId, UpdateReceiptRequest request)
    {
        var receipt = RequireAccessibleReceipt(actor, receiptId);
        if (receipt.Status != ReceiptStatus.Available) throw new InvalidOperationException("Only unattached available receipts can be updated.");

        var fileName = request.FileName ?? receipt.FileName;
        var mimeType = request.MimeType ?? receipt.MimeType;
        var sizeBytes = request.SizeBytes ?? receipt.SizeBytes;
        var checksum = request.ChecksumSha256 ?? receipt.ChecksumSha256;
        var documentType = request.DocumentType ?? receipt.DocumentType;
        var validation = ClaimApiValidation.ValidateDocument(new AttachDocumentRequest(fileName, mimeType, sizeBytes, checksum, documentType));
        if (validation.Count > 0) throw new ArgumentException(validation[0].Issue);

        var updated = receipt with
        {
            FileName = Path.GetFileName(fileName.Trim()),
            MimeType = mimeType.Trim().ToLowerInvariant(),
            SizeBytes = sizeBytes,
            ChecksumSha256 = checksum.Trim().ToLowerInvariant(),
            DocumentType = documentType.Trim(),
            Description = request.Description is null ? receipt.Description : (string.IsNullOrWhiteSpace(request.Description) ? null : request.Description.Trim()),
            UpdatedAt = DateTimeOffset.UtcNow
        };

        repository.UpdateReceipt(updated);
        Audit(actor, "receipt.updated", "success", "receipt", updated.Id, new Dictionary<string, object?>());
        return updated;
    }

    public ReceiptResponse ArchiveReceipt(ActorContext actor, Guid receiptId)
    {
        var receipt = RequireAccessibleReceipt(actor, receiptId);
        if (receipt.Status != ReceiptStatus.Available) throw new InvalidOperationException("Only unattached available receipts can be archived.");

        var timestamp = DateTimeOffset.UtcNow;
        var archived = receipt with { Status = ReceiptStatus.Archived, UpdatedAt = timestamp, ArchivedAt = timestamp };
        repository.UpdateReceipt(archived);
        Audit(actor, "receipt.archived", "success", "receipt", archived.Id, new Dictionary<string, object?>());
        return archived;
    }

    public ClaimDocumentResponse AttachSavedReceiptToExpense(ActorContext actor, Guid claimId, Guid expenseId, Guid receiptId)
    {
        var claim = RequireAccessibleDraft(actor, claimId);
        if (claim.Expenses.All(expense => expense.Id != expenseId)) throw new KeyNotFoundException("Expense was not found on this claim.");
        var receipt = RequireAccessibleReceipt(actor, receiptId);
        if (receipt.Status != ReceiptStatus.Available) throw new InvalidOperationException("Only unattached available receipts can be attached.");

        var document = CreateDocument(expenseId, receipt.Id, new AttachDocumentRequest(receipt.FileName, receipt.MimeType, receipt.SizeBytes, receipt.ChecksumSha256, receipt.DocumentType));
        repository.AttachDocument(claim.Id, expenseId, document);

        var timestamp = DateTimeOffset.UtcNow;
        repository.UpdateReceipt(receipt with { Status = ReceiptStatus.Attached, ClaimId = claim.Id, ExpenseId = expenseId, AttachedAt = timestamp, UpdatedAt = timestamp });
        Audit(actor, "receipt.attached", "success", "receipt", receipt.Id, new Dictionary<string, object?> { ["claim_id"] = claim.Id, ["expense_id"] = expenseId, ["document_id"] = document.Id });
        Audit(actor, "claim_document.attached", "success", "claim", claim.Id, new Dictionary<string, object?> { ["expense_id"] = expenseId, ["document_id"] = document.Id, ["saved_receipt_id"] = receipt.Id });
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
            Audit(actor, "claim.validation_failed", "failure", "claim", claim.Id, new Dictionary<string, object?> { ["details"] = details });
            return new ClaimValidationResult(false, details);
        }

        var submitted = claim with { Status = ClaimStatus.Submitted, SubmittedAt = DateTimeOffset.UtcNow };
        repository.UpdateClaim(submitted);
        Audit(actor, "claim.submitted", "success", "claim", claim.Id, new Dictionary<string, object?> { ["submitted_at"] = submitted.SubmittedAt });
        return new ClaimValidationResult(true, [], submitted);
    }

    public IReadOnlyList<AuditEvent> AuditEventsForClaim(ActorContext actor, Guid claimId)
    {
        var claim = RequireAccessible(actor, claimId);
        return repository.GetAuditEvents("claim", claim.Id);
    }

    public IReadOnlyList<AuditEvent> AuditEventsForEntity(ActorContext actor, string entityType, Guid entityId)
    {
        return entityType switch
        {
            "claim" => AuditEventsForClaim(actor, entityId),
            "receipt" => repository.GetAuditEvents("receipt", RequireAccessibleReceipt(actor, entityId).Id),
            _ => throw new KeyNotFoundException("Entity was not found.")
        };
    }

    private ReceiptResponse RequireAccessibleReceipt(ActorContext actor, Guid receiptId)
    {
        var receipt = repository.GetReceipt(receiptId) ?? throw new KeyNotFoundException("Receipt was not found.");
        if (receipt.AgencyId != actor.AgencyId || (actor.ActorType == "employee" && receipt.EmployeeId != actor.ActorId)) throw new UnauthorizedAccessException("Actor cannot access this receipt.");
        return receipt;
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

    private static ClaimDocumentResponse CreateDocument(Guid expenseId, Guid? savedReceiptId, AttachDocumentRequest request) =>
        new(Guid.NewGuid(), expenseId, savedReceiptId, Path.GetFileName(request.FileName.Trim()), request.MimeType.Trim().ToLowerInvariant(), request.SizeBytes, request.ChecksumSha256.Trim().ToLowerInvariant(), request.DocumentType.Trim(), DateTimeOffset.UtcNow);

    private void Audit(ActorContext actor, string eventType, string outcome, string entityType, Guid entityId, IReadOnlyDictionary<string, object?> data)
    {
        repository.AddAuditEvent(new AuditEvent(Guid.NewGuid(), eventType, outcome, entityType, entityId, actor.ActorType, actor.ActorId, actor.AgencyId, actor.CorrelationId, DateTimeOffset.UtcNow, data));
    }
}
