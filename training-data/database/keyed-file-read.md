---
title: "Reading from a Keyed File"
type: comprehension
generation: all
difficulty: basic
tags: [file-io, keyed-file, read, error-handling]
description: "Read a record by key from a BBj data file"
---

## Code

```bbj
REM Read customer record by ID
custId$ = "CUST001"

OPEN (1)"customers.dat"
READ (1, KEY=custId$, ERR=NOT_FOUND) name$, address$, balance
CLOSE (1)
PRINT "Customer: ", name$
PRINT "Address: ", address$
PRINT "Balance: ", balance
END

NOT_FOUND:
    PRINT "Customer not found: ", custId$
    CLOSE (1, ERR=*NEXT)
END
```

## Expected Output

If the customer exists in the file:

```
Customer: Acme Corp
Address: 123 Main Street
Balance: 1250.00
```

If the customer is not found:

```
Customer not found: CUST001
```

## Explanation

BBj keyed file operations work across all generations, from Character mode to DWC:

1. **Channel number**: The `(1)` is a file channel - an integer identifying the open file. Channels 1-255 are available for user files.

2. **OPEN statement**: Opens the file and associates it with channel 1. The file must exist.

3. **KEY clause**: `KEY=custId$` positions to the record with the specified key value. This is the primary record lookup mechanism in keyed files.

4. **ERR clause**: `ERR=NOT_FOUND` branches to the label if the key is not found (error 11). This prevents the program from crashing on missing records.

5. **Field list**: `name$, address$, balance` receives values in the order they were written to the file. String variables end with `$`, numeric variables don't.

6. **CLOSE statement**: Always close files to release system resources. The `ERR=*NEXT` in the error handler prevents errors if the file wasn't successfully opened.

7. **END statement**: Terminates the program. Without this, execution would fall through to the `NOT_FOUND` label.

This pattern is fundamental to BBj data access and predates SQL/ADO approaches while remaining fully supported.
