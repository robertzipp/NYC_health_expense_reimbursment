namespace Hcfsa.Api.Claims;

public sealed record ActorContext(string ActorType, string ActorId, string AgencyId, string? CorrelationId)
{
    public static ActorContext FromHeaders(IHeaderDictionary headers)
    {
        return new ActorContext(
            Required(headers, "X-Actor-Type"),
            Required(headers, "X-Actor-Id"),
            Required(headers, "X-Agency-Id"),
            headers.TryGetValue("X-Correlation-Id", out var correlationId) ? correlationId.ToString() : null);
    }

    private static string Required(IHeaderDictionary headers, string name) =>
        headers.TryGetValue(name, out var value) && !string.IsNullOrWhiteSpace(value)
            ? value.ToString()
            : throw new BadHttpRequestException($"Missing required header {name}", StatusCodes.Status400BadRequest);
}

public enum ClaimStatus { Draft, Submitted }

public sealed record CreateClaimRequest(string EmployeeId);

public sealed record AddExpenseRequest(
    string Claimant,
    DateOnly DateOfService,
    string ExpenseCategory,
    decimal AmountCharged,
    decimal RequestedReimbursementAmount,
    string ServiceType,
    bool? DocumentationRequired);

public sealed record AttachDocumentRequest(
    string FileName,
    string MimeType,
    long SizeBytes,
    string ChecksumSha256,
    string DocumentType);

public sealed record ClaimResponse(
    Guid Id,
    string AgencyId,
    string EmployeeId,
    ClaimStatus Status,
    DateTimeOffset CreatedAt,
    DateTimeOffset? SubmittedAt,
    IReadOnlyList<ClaimExpenseResponse> Expenses);

public sealed record ClaimExpenseResponse(
    Guid Id,
    string Claimant,
    DateOnly DateOfService,
    string ExpenseCategory,
    decimal AmountCharged,
    decimal RequestedReimbursementAmount,
    string ServiceType,
    bool DocumentationRequired,
    IReadOnlyList<ClaimDocumentResponse> Documents);

public sealed record ClaimDocumentResponse(
    Guid Id,
    Guid ExpenseId,
    string FileName,
    string MimeType,
    long SizeBytes,
    string ChecksumSha256,
    string DocumentType,
    DateTimeOffset AttachedAt);

public sealed record ValidationDetail(string Field, string Issue);

public sealed record ClaimValidationResult(bool IsValid, IReadOnlyList<ValidationDetail> Details, ClaimResponse? Claim = null);

public sealed record AuditEvent(
    Guid Id,
    string EventType,
    string Outcome,
    string EntityType,
    Guid EntityId,
    string ActorType,
    string ActorId,
    string AgencyId,
    string? CorrelationId,
    DateTimeOffset OccurredAt,
    IReadOnlyDictionary<string, object?> Data);

public static class ErrorEnvelope
{
    public static object Validation(IReadOnlyList<ValidationDetail> details) =>
        new { error = new { code = "VALIDATION_ERROR", message = "Request validation failed.", details } };

    public static object BusinessRule(IReadOnlyList<ValidationDetail> details) =>
        new { error = new { code = "BUSINESS_RULE_VIOLATION", message = "Claim cannot be submitted.", details } };
}
