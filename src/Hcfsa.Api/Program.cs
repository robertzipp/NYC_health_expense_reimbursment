using Hcfsa.Api.Claims;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton<IClaimRepository, InMemoryClaimRepository>();
builder.Services.AddSingleton<ClaimService>();

var app = builder.Build();

app.UseExceptionHandler(errorApp =>
{
    errorApp.Run(async context =>
    {
        var exception = context.Features.Get<Microsoft.AspNetCore.Diagnostics.IExceptionHandlerFeature>()?.Error;
        var (status, code, message) = exception switch
        {
            BadHttpRequestException => (StatusCodes.Status400BadRequest, "VALIDATION_ERROR", "Request validation failed."),
            ArgumentException => (StatusCodes.Status400BadRequest, "VALIDATION_ERROR", "Request validation failed."),
            UnauthorizedAccessException => (StatusCodes.Status403Forbidden, "FORBIDDEN", "Actor is not allowed to access this resource."),
            KeyNotFoundException => (StatusCodes.Status404NotFound, "NOT_FOUND", "Resource was not found."),
            InvalidOperationException => (StatusCodes.Status409Conflict, "CONFLICT", "Requested state transition is not allowed."),
            _ => (StatusCodes.Status500InternalServerError, "INTERNAL_ERROR", "An unexpected error occurred.")
        };

        context.Response.StatusCode = status;
        await context.Response.WriteAsJsonAsync(new
        {
            error = new
            {
                code,
                message,
                details = exception is ArgumentException argument ? new[] { new { field = "request", issue = argument.Message } } : []
            }
        });
    });
});

var claims = app.MapGroup("/api/v1/claims");
var receipts = app.MapGroup("/api/v1/receipts");

claims.MapPost("/", (CreateClaimRequest request, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var result = service.CreateClaim(actor, request);
    return Results.Created($"/api/v1/claims/{result.Id}", result);
});

claims.MapGet("/{claimId:guid}", (Guid claimId, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return service.GetClaim(actor, claimId) is { } claim ? Results.Ok(claim) : Results.NotFound();
});

claims.MapPost("/{claimId:guid}/expenses", (Guid claimId, AddExpenseRequest request, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var validation = ClaimApiValidation.ValidateExpense(request);
    if (validation.Count > 0) return Results.BadRequest(ErrorEnvelope.Validation(validation));

    var result = service.AddExpense(actor, claimId, request);
    return Results.Created($"/api/v1/claims/{claimId}/expenses/{result.Id}", result);
});

claims.MapPost("/{claimId:guid}/expenses/{expenseId:guid}/documents", (Guid claimId, Guid expenseId, AttachDocumentRequest request, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var validation = ClaimApiValidation.ValidateDocument(request);
    if (validation.Count > 0) return Results.BadRequest(ErrorEnvelope.Validation(validation));

    var result = service.AttachDocument(actor, claimId, expenseId, request);
    return Results.Created($"/api/v1/claims/{claimId}/expenses/{expenseId}/documents/{result.Id}", result);
});

claims.MapPost("/{claimId:guid}/expenses/{expenseId:guid}/saved-receipts/{receiptId:guid}", (Guid claimId, Guid expenseId, Guid receiptId, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var result = service.AttachSavedReceiptToExpense(actor, claimId, expenseId, receiptId);
    return Results.Created($"/api/v1/claims/{claimId}/expenses/{expenseId}/documents/{result.Id}", result);
});

claims.MapPost("/{claimId:guid}/validate", (Guid claimId, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return Results.Ok(service.ValidateClaim(actor, claimId));
});

claims.MapPost("/{claimId:guid}/submit", (Guid claimId, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var result = service.SubmitClaim(actor, claimId);
    return result.IsValid ? Results.Ok(result.Claim) : Results.UnprocessableEntity(ErrorEnvelope.BusinessRule(result.Details));
});

receipts.MapPost("/", (CreateReceiptRequest request, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    var validation = ClaimApiValidation.ValidateDocument(new AttachDocumentRequest(request.FileName, request.MimeType, request.SizeBytes, request.ChecksumSha256, request.DocumentType));
    if (validation.Count > 0) return Results.BadRequest(ErrorEnvelope.Validation(validation));

    var result = service.CreateReceipt(actor, request);
    return Results.Created($"/api/v1/receipts/{result.Id}", result);
});

receipts.MapGet("/", (bool? includeArchived, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return Results.Ok(new { data = service.ListReceipts(actor, includeArchived ?? false) });
});

receipts.MapMethods("/{receiptId:guid}", ["PATCH", "PUT"], (Guid receiptId, UpdateReceiptRequest request, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return Results.Ok(service.UpdateReceipt(actor, receiptId, request));
});

receipts.MapPost("/{receiptId:guid}/archive", (Guid receiptId, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return Results.Ok(service.ArchiveReceipt(actor, receiptId));
});

app.MapGet("/api/v1/audit-events", (Guid entityId, string? entityType, HttpContext http, ClaimService service) =>
{
    var actor = ActorContext.FromHeaders(http.Request.Headers);
    return Results.Ok(new { data = service.AuditEventsForEntity(actor, entityType ?? "claim", entityId) });
});

app.Run();
