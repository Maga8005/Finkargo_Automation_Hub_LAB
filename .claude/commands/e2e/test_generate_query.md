# E2E Test: Generate Query Feature

Test the random natural language query generation functionality in the Natural Language SQL Interface application.

## User Story

As a user
I want a button that generates random natural language queries based on my database schema
So that I can explore my data with interesting query examples without having to think of questions myself

## Test Steps

1. Navigate to the `Application URL`
2. Take a screenshot of the initial state
3. **Verify** the page title is "Natural Language SQL Interface"
4. **Verify** core UI elements are present:
   - Query input textbox
   - Query button
   - Generate Query button
   - Upload Data button
   - Available Tables section

5. **Verify** Generate Query button is visible and clickable
6. Take a screenshot showing the Generate Query button

7. Upload sample data to ensure database has tables:
   - Click "Upload Data" button
   - Click on one of the sample data buttons (e.g., "Users Data" or "Product Inventory")
   - Wait for upload to complete
   - **Verify** table appears in Available Tables section

8. Click the "Generate Query" button
9. **Verify** button shows loading state during generation
10. Wait for query generation to complete
11. **Verify** query input field is populated with generated text
12. **Verify** generated text is not empty
13. **Verify** generated text appears to be a natural language query (contains question words or imperative verbs)
14. Take a screenshot of the populated query input

15. Test query overwrite behavior:
    - Manually type some text into the query input field
    - Click "Generate Query" button again
    - **Verify** the previous text is completely overwritten (not appended)
    - Take a screenshot showing the new generated query

16. Test generated query execution:
    - With a generated query in the input field, click "Query" button
    - **Verify** the query executes without errors OR shows a graceful error message
    - **Verify** SQL translation is displayed
    - **Verify** results appear (if query is valid) or error message is shown
    - Take a screenshot of the query results

17. Test error handling (empty database):
    - Remove all tables from the database (click X on each table)
    - Click "Generate Query" button
    - **Verify** an appropriate error message is displayed (e.g., "No tables available")
    - Take a screenshot of the error message

## Success Criteria
- Generate Query button is visible and properly styled
- Button is positioned between Query and Upload Data buttons
- Button shows loading state during generation
- Query input field is populated with generated text (overwrites existing content)
- Generated query is limited to 2 sentences maximum
- Generated query can be executed by clicking Query button
- Error handling works when no tables exist
- Button is disabled during generation to prevent multiple simultaneous requests
- At least 5 screenshots are taken

## Expected Behavior
- Generated queries should be varied and contextually relevant to the database schema
- Queries should showcase different patterns: aggregations, filters, sorting, etc.
- If multiple tables exist, queries may occasionally suggest joins
- Generated queries should be natural language, not SQL code
- The feature should handle edge cases gracefully (empty database, API failures)

## Notes
- Query generation may take 1-3 seconds depending on LLM API response time
- Generated queries will vary each time the button is clicked due to high temperature setting
- Requires either OPENAI_API_KEY or ANTHROPIC_API_KEY to be configured
