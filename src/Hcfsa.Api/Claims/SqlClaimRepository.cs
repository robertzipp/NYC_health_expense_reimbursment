using System.Data;

namespace Hcfsa.Api.Claims;

public sealed class SqlClaimRepository(IDbConnection connection) : IClaimRepository
{
    public ClaimResponse? GetClaim(Guid claimId)
    {
        var claim = ReadClaim(claimId);
        if (claim is null) return null;

        var expenses = ReadExpenses(claimId)
            .Select(expense => expense with { Documents = ReadDocuments(expense.Id) })
            .ToArray();
        return claim with { Expenses = expenses };
    }

    public void SaveClaim(ClaimResponse claim)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO dbo.Claims (ClaimId, AgencyId, EmployeeId, Status, CreatedAtUtc, SubmittedAtUtc)
            VALUES (@ClaimId, @AgencyId, @EmployeeId, @Status, @CreatedAtUtc, @SubmittedAtUtc)
            """;
        Add(command, "@ClaimId", claim.Id);
        Add(command, "@AgencyId", claim.AgencyId);
        Add(command, "@EmployeeId", claim.EmployeeId);
        Add(command, "@Status", claim.Status.ToString());
        Add(command, "@CreatedAtUtc", claim.CreatedAt.UtcDateTime);
        Add(command, "@SubmittedAtUtc", DBNull.Value);
        command.ExecuteNonQuery();
    }

    public void UpdateClaim(ClaimResponse claim)
    {
        using var command = connection.CreateCommand();
        command.CommandText = "UPDATE dbo.Claims SET Status = @Status, SubmittedAtUtc = @SubmittedAtUtc WHERE ClaimId = @ClaimId";
        Add(command, "@ClaimId", claim.Id);
        Add(command, "@Status", claim.Status.ToString());
        Add(command, "@SubmittedAtUtc", claim.SubmittedAt?.UtcDateTime ?? (object)DBNull.Value);
        command.ExecuteNonQuery();
    }

    public void AddExpense(Guid claimId, ClaimExpenseResponse expense)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO dbo.ClaimExpenses
                (ExpenseId, ClaimId, Claimant, DateOfService, ExpenseCategory, AmountChargedCents,
                 RequestedReimbursementCents, ServiceType, DocumentationRequired, CreatedAtUtc)
            VALUES
                (@ExpenseId, @ClaimId, @Claimant, @DateOfService, @ExpenseCategory, @AmountChargedCents,
                 @RequestedReimbursementCents, @ServiceType, @DocumentationRequired, @CreatedAtUtc)
            """;
        Add(command, "@ExpenseId", expense.Id);
        Add(command, "@ClaimId", claimId);
        Add(command, "@Claimant", expense.Claimant);
        Add(command, "@DateOfService", expense.DateOfService.ToDateTime(TimeOnly.MinValue));
        Add(command, "@ExpenseCategory", expense.ExpenseCategory);
        Add(command, "@AmountChargedCents", ToCents(expense.AmountCharged));
        Add(command, "@RequestedReimbursementCents", ToCents(expense.RequestedReimbursementAmount));
        Add(command, "@ServiceType", expense.ServiceType);
        Add(command, "@DocumentationRequired", expense.DocumentationRequired);
        Add(command, "@CreatedAtUtc", DateTime.UtcNow);
        command.ExecuteNonQuery();
    }

    public void AttachDocument(Guid claimId, Guid expenseId, ClaimDocumentResponse document)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO dbo.ClaimDocuments
                (DocumentId, ClaimId, ExpenseId, SavedReceiptId, FileName, MimeType, SizeBytes, ChecksumSha256, DocumentType, AttachedAtUtc)
            VALUES
                (@DocumentId, @ClaimId, @ExpenseId, @SavedReceiptId, @FileName, @MimeType, @SizeBytes, @ChecksumSha256, @DocumentType, @AttachedAtUtc)
            """;
        Add(command, "@DocumentId", document.Id);
        Add(command, "@ClaimId", claimId);
        Add(command, "@ExpenseId", expenseId);
        Add(command, "@SavedReceiptId", document.SavedReceiptId);
        Add(command, "@FileName", document.FileName);
        Add(command, "@MimeType", document.MimeType);
        Add(command, "@SizeBytes", document.SizeBytes);
        Add(command, "@ChecksumSha256", document.ChecksumSha256);
        Add(command, "@DocumentType", document.DocumentType);
        Add(command, "@AttachedAtUtc", document.AttachedAt.UtcDateTime);
        command.ExecuteNonQuery();
    }

    public ReceiptResponse? GetReceipt(Guid receiptId)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT ReceiptId, AgencyId, EmployeeId, FileName, MimeType, SizeBytes, ChecksumSha256, DocumentType, Description,
                   Status, ClaimId, ExpenseId, CreatedAtUtc, UpdatedAtUtc, AttachedAtUtc, ArchivedAtUtc
            FROM dbo.SavedReceipts
            WHERE ReceiptId = @ReceiptId
            """;
        Add(command, "@ReceiptId", receiptId);
        using var reader = command.ExecuteReader();
        return reader.Read() ? ReadReceipt(reader) : null;
    }

    public IReadOnlyList<ReceiptResponse> ListReceipts(string agencyId, string employeeId, bool includeArchived)
    {
        using var command = connection.CreateCommand();
        command.CommandText = $"""
            SELECT ReceiptId, AgencyId, EmployeeId, FileName, MimeType, SizeBytes, ChecksumSha256, DocumentType, Description,
                   Status, ClaimId, ExpenseId, CreatedAtUtc, UpdatedAtUtc, AttachedAtUtc, ArchivedAtUtc
            FROM dbo.SavedReceipts
            WHERE AgencyId = @AgencyId AND EmployeeId = @EmployeeId {(includeArchived ? "" : "AND Status <> 'Archived'")}
            ORDER BY CreatedAtUtc, ReceiptId
            """;
        Add(command, "@AgencyId", agencyId);
        Add(command, "@EmployeeId", employeeId);
        using var reader = command.ExecuteReader();
        var receipts = new List<ReceiptResponse>();
        while (reader.Read()) receipts.Add(ReadReceipt(reader));
        return receipts;
    }

    public void SaveReceipt(ReceiptResponse receipt)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO dbo.SavedReceipts
                (ReceiptId, AgencyId, EmployeeId, FileName, MimeType, SizeBytes, ChecksumSha256, DocumentType, Description,
                 Status, ClaimId, ExpenseId, CreatedAtUtc, UpdatedAtUtc, AttachedAtUtc, ArchivedAtUtc)
            VALUES
                (@ReceiptId, @AgencyId, @EmployeeId, @FileName, @MimeType, @SizeBytes, @ChecksumSha256, @DocumentType, @Description,
                 @Status, @ClaimId, @ExpenseId, @CreatedAtUtc, @UpdatedAtUtc, @AttachedAtUtc, @ArchivedAtUtc)
            """;
        WriteReceiptParameters(command, receipt);
        command.ExecuteNonQuery();
    }

    public void UpdateReceipt(ReceiptResponse receipt)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            UPDATE dbo.SavedReceipts
            SET FileName = @FileName, MimeType = @MimeType, SizeBytes = @SizeBytes, ChecksumSha256 = @ChecksumSha256,
                DocumentType = @DocumentType, Description = @Description, Status = @Status, ClaimId = @ClaimId,
                ExpenseId = @ExpenseId, UpdatedAtUtc = @UpdatedAtUtc, AttachedAtUtc = @AttachedAtUtc, ArchivedAtUtc = @ArchivedAtUtc
            WHERE ReceiptId = @ReceiptId
            """;
        WriteReceiptParameters(command, receipt);
        command.ExecuteNonQuery();
    }

    public void AddAuditEvent(AuditEvent auditEvent)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            INSERT INTO dbo.AuditEvents
                (AuditEventId, EventType, Outcome, EntityType, EntityId, ActorType, ActorId, AgencyId, CorrelationId, OccurredAtUtc)
            VALUES
                (@AuditEventId, @EventType, @Outcome, @EntityType, @EntityId, @ActorType, @ActorId, @AgencyId, @CorrelationId, @OccurredAtUtc)
            """;
        Add(command, "@AuditEventId", auditEvent.Id);
        Add(command, "@EventType", auditEvent.EventType);
        Add(command, "@Outcome", auditEvent.Outcome);
        Add(command, "@EntityType", auditEvent.EntityType);
        Add(command, "@EntityId", auditEvent.EntityId);
        Add(command, "@ActorType", auditEvent.ActorType);
        Add(command, "@ActorId", auditEvent.ActorId);
        Add(command, "@AgencyId", auditEvent.AgencyId);
        Add(command, "@CorrelationId", auditEvent.CorrelationId);
        Add(command, "@OccurredAtUtc", auditEvent.OccurredAt.UtcDateTime);
        command.ExecuteNonQuery();
    }

    public IReadOnlyList<AuditEvent> GetAuditEvents(string entityType, Guid entityId)
    {
        using var command = connection.CreateCommand();
        command.CommandText = """
            SELECT AuditEventId, EventType, Outcome, EntityType, EntityId, ActorType, ActorId, AgencyId, CorrelationId, OccurredAtUtc
            FROM dbo.AuditEvents
            WHERE EntityType = @EntityType AND EntityId = @EntityId
            ORDER BY OccurredAtUtc, AuditEventId
            """;
        Add(command, "@EntityType", entityType);
        Add(command, "@EntityId", entityId);
        using var reader = command.ExecuteReader();
        var events = new List<AuditEvent>();
        while (reader.Read())
        {
            events.Add(new AuditEvent(reader.GetGuid(0), reader.GetString(1), reader.GetString(2), reader.GetString(3), reader.GetGuid(4), reader.GetString(5), reader.GetString(6), reader.GetString(7), reader.IsDBNull(8) ? null : reader.GetString(8), new DateTimeOffset(reader.GetDateTime(9), TimeSpan.Zero), new Dictionary<string, object?>()));
        }
        return events;
    }

    private ClaimResponse? ReadClaim(Guid claimId)
    {
        using var command = connection.CreateCommand();
        command.CommandText = "SELECT ClaimId, AgencyId, EmployeeId, Status, CreatedAtUtc, SubmittedAtUtc FROM dbo.Claims WHERE ClaimId = @ClaimId";
        Add(command, "@ClaimId", claimId);
        using var reader = command.ExecuteReader();
        return reader.Read()
            ? new ClaimResponse(reader.GetGuid(0), reader.GetString(1), reader.GetString(2), Enum.Parse<ClaimStatus>(reader.GetString(3)), new DateTimeOffset(reader.GetDateTime(4), TimeSpan.Zero), reader.IsDBNull(5) ? null : new DateTimeOffset(reader.GetDateTime(5), TimeSpan.Zero), [])
            : null;
    }

    private IReadOnlyList<ClaimExpenseResponse> ReadExpenses(Guid claimId)
    {
        using var command = connection.CreateCommand();
        command.CommandText = "SELECT ExpenseId, Claimant, DateOfService, ExpenseCategory, AmountChargedCents, RequestedReimbursementCents, ServiceType, DocumentationRequired FROM dbo.ClaimExpenses WHERE ClaimId = @ClaimId ORDER BY CreatedAtUtc, ExpenseId";
        Add(command, "@ClaimId", claimId);
        using var reader = command.ExecuteReader();
        var expenses = new List<ClaimExpenseResponse>();
        while (reader.Read())
        {
            expenses.Add(new ClaimExpenseResponse(reader.GetGuid(0), reader.GetString(1), DateOnly.FromDateTime(reader.GetDateTime(2)), reader.GetString(3), FromCents(reader.GetInt32(4)), FromCents(reader.GetInt32(5)), reader.GetString(6), reader.GetBoolean(7), []));
        }
        return expenses;
    }

    private IReadOnlyList<ClaimDocumentResponse> ReadDocuments(Guid expenseId)
    {
        using var command = connection.CreateCommand();
        command.CommandText = "SELECT DocumentId, ExpenseId, SavedReceiptId, FileName, MimeType, SizeBytes, ChecksumSha256, DocumentType, AttachedAtUtc FROM dbo.ClaimDocuments WHERE ExpenseId = @ExpenseId ORDER BY AttachedAtUtc, DocumentId";
        Add(command, "@ExpenseId", expenseId);
        using var reader = command.ExecuteReader();
        var documents = new List<ClaimDocumentResponse>();
        while (reader.Read())
        {
            documents.Add(new ClaimDocumentResponse(reader.GetGuid(0), reader.GetGuid(1), reader.IsDBNull(2) ? null : reader.GetGuid(2), reader.GetString(3), reader.GetString(4), reader.GetInt64(5), reader.GetString(6), reader.GetString(7), new DateTimeOffset(reader.GetDateTime(8), TimeSpan.Zero)));
        }
        return documents;
    }

    private static ReceiptResponse ReadReceipt(IDataRecord reader) =>
        new(
            reader.GetGuid(0), reader.GetString(1), reader.GetString(2), reader.GetString(3), reader.GetString(4), reader.GetInt64(5),
            reader.GetString(6), reader.GetString(7), reader.IsDBNull(8) ? null : reader.GetString(8), Enum.Parse<ReceiptStatus>(reader.GetString(9)),
            reader.IsDBNull(10) ? null : reader.GetGuid(10), reader.IsDBNull(11) ? null : reader.GetGuid(11),
            new DateTimeOffset(reader.GetDateTime(12), TimeSpan.Zero), new DateTimeOffset(reader.GetDateTime(13), TimeSpan.Zero),
            reader.IsDBNull(14) ? null : new DateTimeOffset(reader.GetDateTime(14), TimeSpan.Zero),
            reader.IsDBNull(15) ? null : new DateTimeOffset(reader.GetDateTime(15), TimeSpan.Zero));

    private static void WriteReceiptParameters(IDbCommand command, ReceiptResponse receipt)
    {
        Add(command, "@ReceiptId", receipt.Id);
        Add(command, "@AgencyId", receipt.AgencyId);
        Add(command, "@EmployeeId", receipt.EmployeeId);
        Add(command, "@FileName", receipt.FileName);
        Add(command, "@MimeType", receipt.MimeType);
        Add(command, "@SizeBytes", receipt.SizeBytes);
        Add(command, "@ChecksumSha256", receipt.ChecksumSha256);
        Add(command, "@DocumentType", receipt.DocumentType);
        Add(command, "@Description", receipt.Description);
        Add(command, "@Status", receipt.Status.ToString());
        Add(command, "@ClaimId", receipt.ClaimId);
        Add(command, "@ExpenseId", receipt.ExpenseId);
        Add(command, "@CreatedAtUtc", receipt.CreatedAt.UtcDateTime);
        Add(command, "@UpdatedAtUtc", receipt.UpdatedAt.UtcDateTime);
        Add(command, "@AttachedAtUtc", receipt.AttachedAt?.UtcDateTime ?? (object)DBNull.Value);
        Add(command, "@ArchivedAtUtc", receipt.ArchivedAt?.UtcDateTime ?? (object)DBNull.Value);
    }

    private static int ToCents(decimal amount) => checked((int)Math.Round(amount * 100m, MidpointRounding.AwayFromZero));
    private static decimal FromCents(int cents) => cents / 100m;

    private static void Add(IDbCommand command, string name, object? value)
    {
        var parameter = command.CreateParameter();
        parameter.ParameterName = name;
        parameter.Value = value ?? DBNull.Value;
        command.Parameters.Add(parameter);
    }
}
