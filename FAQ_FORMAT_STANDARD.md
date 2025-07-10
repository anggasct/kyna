# FAQ Document Format Standard

This document defines the universal format standard for FAQ documents that can be processed optimally by the RAG system, regardless of language.

## 1. Basic Structure

### Required Elements

- Document title containing "FAQ" keyword
- Questions formatted as markdown headers (##)
- Questions must end with question mark (?)
- Answers immediately follow questions without additional headers

### Format Template

```markdown
# FAQ [Topic Name]

## [Question 1]?

[Detailed answer with all necessary information]

## [Question 2]?

[Detailed answer with all necessary information]
```

## 2. Universal Detection Criteria

The system detects FAQ documents based on these language-agnostic patterns:

### High Priority Indicators (Score: 3 each)

- ✅ Explicit "FAQ" keyword in document
- ✅ "Frequently Asked Questions" phrase
- ✅ Q: / Question: format
- ✅ A: / Answer: format

### Medium Priority Indicators (Score: 1 per occurrence)

- ✅ Markdown headers ending with question mark (## ...?)
- ✅ Q&A structural pattern (question followed by non-header content)

### Low Priority Indicators (Score: 1 total)

- ✅ Multiple question marks (3+ in document)

**Detection Threshold:** Minimum score of 3 to classify as FAQ

## 3. Optimal FAQ Formats

### Format A: Standard Q&A

```markdown
# FAQ Hotel Services

## What room types are available?

We offer 3 room types:
- Standard Room: Basic amenities
- Deluxe Room: Enhanced comfort  
- Suite Room: Premium experience

All rooms include free breakfast and WiFi.

## How can I make a reservation?

You can book through:
1. Our website (24/7 available)
2. Mobile app
3. Phone: +1-234-567-8900
4. Email: reservations@hotel.com
```

### Format B: Multiple Question Variations

```markdown
## What payment methods do you accept? / How can I pay? / Payment options?

We accept various payment methods:

**Credit Cards:** Visa, Mastercard, American Express
**Digital Payments:** PayPal, Apple Pay, Google Pay
**Bank Transfer:** Direct bank transfer
**Cash:** Accepted at check-in

All payments are secure and encrypted.
```

### Format C: Structured Answers

```markdown
## What are your check-in and check-out times?

**Standard Schedule:**
- Check-in: 3:00 PM onwards
- Check-out: 12:00 PM (noon)

**Early Check-in:**
- Available based on room availability
- Additional charges may apply before 10:00 AM

**Late Check-out:**
- Until 3:00 PM: 25% of room rate
- Until 6:00 PM: 50% of room rate
```

## 4. Multi-language Support

### Language-Agnostic Principles

- Structure-based detection (not keyword-dependent)
- Markdown header format consistency
- Question mark usage universal
- Consistent Q&A pairing

### Examples in Different Languages

#### English

```markdown
## What facilities do you offer?
```

#### Indonesian

```markdown
## Fasilitas apa saja yang tersedia?
```

#### Spanish

```markdown
## ¿Qué instalaciones ofrecen?
```

#### French

```markdown
## Quelles installations proposez-vous ?
```

## 5. Processing Optimization

### Chunk Size Guidelines

- **Optimal chunk size:** 800-1600 characters
- **Keep Q&A pairs together** in single chunks
- **Preserve context** by including question in answer chunks

### Metadata Enhancement

```markdown
## Question with metadata

**Category:** Room Services
**Keywords:** room types, booking, availability
**Related:** reservations, pricing

[Answer content here]
```

## 6. Common Pitfalls to Avoid

### ❌ Don't Do This

```markdown
## Question without question mark
Answer here

### Sub-header breaking Q&A pairs
More content here
```

### ❌ Avoid These Patterns

- Questions without question marks
- Sub-headers between Q&A pairs
- Mixing FAQ with other content types
- Inconsistent header levels

### ✅ Best Practices

- Always end questions with ?
- Keep answers comprehensive but concise
- Use consistent header levels (##)
- Include variations of common questions
- Provide specific, actionable information

## 7. Validation Checklist

Before uploading FAQ documents, ensure:

- [ ] Document title contains "FAQ"
- [ ] All questions use ## headers
- [ ] All questions end with ?
- [ ] Answers immediately follow questions
- [ ] No sub-headers between Q&A pairs
- [ ] Consistent formatting throughout
- [ ] Comprehensive answers with specific details
- [ ] Question variations included where relevant

## 8. Performance Metrics

Well-formatted FAQ documents should achieve:

- **Detection accuracy:** 95%+ correct FAQ classification
- **Retrieval accuracy:** 90%+ relevant answer retrieval
- **Answer completeness:** Full context preserved in responses
- **Multi-language support:** Language-agnostic processing

This standard ensures optimal performance across all languages and content types.
