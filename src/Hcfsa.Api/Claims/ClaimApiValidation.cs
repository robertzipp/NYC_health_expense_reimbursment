using System.Text.RegularExpressions;

namespace Hcfsa.Api.Claims;

public static partial class ClaimApiValidation
{
    private static readonly HashSet<string> SupportedMimeTypes = new(StringComparer.OrdinalIgnoreCase)
    {
        "application/pdf",
        "image/jpeg",
        "image/png"
    };

    public static List<ValidationDetail> ValidateExpense(AddExpenseRequest request)
    {
        var details = new List<ValidationDetail>();
        Required(request.Claimant, "claimant", details);
        Required(request.ExpenseCategory, "expense_category", details);
        Required(request.ServiceType, "service_type", details);

        if (request.AmountCharged <= 0) details.Add(new("amount_charged", "must be greater than 0"));
        if (request.RequestedReimbursementAmount <= 0) details.Add(new("requested_reimbursement_amount", "must be greater than 0"));
        if (request.RequestedReimbursementAmount > request.AmountCharged)
        {
            details.Add(new("requested_reimbursement_amount", "must not exceed amount charged"));
        }

        return details;
    }

    public static List<ValidationDetail> ValidateDocument(AttachDocumentRequest request)
    {
        var details = new List<ValidationDetail>();
        Required(request.FileName, "file_name", details);
        Required(request.DocumentType, "document_type", details);

        if (request.FileName.Contains('/') || request.FileName.Contains('\\'))
        {
            details.Add(new("file_name", "must be a file name without path segments"));
        }

        if (!SupportedMimeTypes.Contains(request.MimeType))
        {
            details.Add(new("mime_type", "unsupported file type"));
        }

        if (request.SizeBytes <= 0) details.Add(new("size_bytes", "must be greater than 0"));
        if (!Sha256Regex().IsMatch(request.ChecksumSha256 ?? string.Empty))
        {
            details.Add(new("checksum_sha256", "must be a 64-character hexadecimal SHA-256"));
        }

        return details;
    }

    private static void Required(string? value, string field, ICollection<ValidationDetail> details)
    {
        if (string.IsNullOrWhiteSpace(value)) details.Add(new(field, "is required"));
    }

    [GeneratedRegex("^[a-fA-F0-9]{64}$")]
    private static partial Regex Sha256Regex();
}
