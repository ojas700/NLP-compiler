#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "compiler_common.h"
#include "lexer.h"
#include "parser.h"
#include "symbol_table.h"
#include "semantic.h"
#include "ir_gen.h"
#include "codegen_c.h"

int main(int argc, char *argv[])
{
    FILE *srcFile = stdin;
    const char *outCFile = "output/generated.c";

    if (argc >= 2) {
        srcFile = fopen(argv[1], "r");
        if (!srcFile) {
            fprintf(stderr, "Error: Could not open input file '%s'\n", argv[1]);
            return 1;
        }
    }
    if (argc >= 3) {
        outCFile = argv[2];
    }

    ILInstruction instructions[MAX_CODE_LINES];
    int instCount = 0;
    char lineBuffer[MAX_LINE_LEN];
    int lineNo = 1;

    initSymbolTable();
    initSemantic();
    initIR();

    printf("========================================\n");
    printf("         NLP COMPILER PIPELINE          \n");
    printf("========================================\n");

    printf("\n[STAGE 1] Lexical & Syntax Analysis (Parsing)...\n");

    int parseError = 0;
    while (fgets(lineBuffer, sizeof(lineBuffer), srcFile)) {
        // Strip newline
        lineBuffer[strcspn(lineBuffer, "\r\n")] = '\0';
        if (strlen(lineBuffer) == 0) {
            lineNo++;
            continue;
        }

        printf("Line %2d: %-30s | Tokens: ", lineNo, lineBuffer);
        tokenize(lineBuffer);

        ILInstruction inst;
        int res = parseLine(lineBuffer, lineNo, &inst);
        if (res < 0) {
            parseError = 1;
            break;
        } else if (res > 0) {
            if (instCount < MAX_CODE_LINES) {
                instructions[instCount++] = inst;
            }
        }
        lineNo++;
    }

    if (srcFile != stdin) {
        fclose(srcFile);
    }

    if (parseError) {
        fprintf(stderr, "\n[FATAL] Parsing failed with syntax errors.\n");
        return 1;
    }
    printf("[SUCCESS] All %d statements parsed successfully.\n", instCount);

    printf("\n[STAGE 2] Semantic Analysis & Symbol Table...\n");
    for (int i = 0; i < instCount; i++) {
        analyzeInstruction(&instructions[i]);
    }

    semanticReport();
    displaySymbolTable();

    if (semanticErrors > 0) {
        fprintf(stderr, "\n[FATAL] Compilation aborted due to semantic errors.\n");
        return 2;
    }

    printf("\n[STAGE 3] Intermediate Representation (IR / 3-Address Code)...\n");
    generateIR(instructions, instCount);
    displayIR();

    printf("\n[STAGE 4] Deterministic C Code Generation...\n");
    if (generateCCode(instructions, instCount, outCFile) != 0) {
        fprintf(stderr, "[FATAL] Failed to write generated C code to '%s'.\n", outCFile);
        return 3;
    }
    printf("[SUCCESS] C source emitted to: %s\n", outCFile);
    printf("========================================\n");
    printf("       COMPILER PIPELINE COMPLETED      \n");
    printf("========================================\n");

    return 0;
}