#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "semantic.h"

int semanticErrors = 0;
static int blockDepth = 0;

void initSemantic()
{
    semanticErrors = 0;
    blockDepth = 0;
}

static void checkVarUsed(const char *name, int line)
{
    if (findSymbol((char *)name) == -1) {
        fprintf(stderr, "[SEMANTIC ERROR Line %d] Variable '%s' not declared.\n", line, name);
        semanticErrors++;
    } else {
        updateUsage((char *)name, line);
    }
}

static void checkExpressionVars(const char *expr, int line)
{
    // Extract tokens that look like variable identifiers
    char token[64];
    int ti = 0;
    for (int i = 0; ; i++) {
        char c = expr[i];
        if (isalpha((unsigned char)c) || c == '_') {
            if (ti < (int)sizeof(token) - 1) {
                token[ti++] = c;
            }
        } else if (isdigit((unsigned char)c) && ti > 0) {
            if (ti < (int)sizeof(token) - 1) {
                token[ti++] = c;
            }
        } else {
            if (ti > 0) {
                token[ti] = '\0';
                checkVarUsed(token, line);
                ti = 0;
            }
        }
        if (c == '\0') break;
    }
}

int analyzeInstruction(const ILInstruction *inst)
{
    int line = inst->line_number;

    switch (inst->type) {
        case CMD_DECLARE:
            if (findSymbol((char *)inst->arg2) != -1) {
                fprintf(stderr, "[SEMANTIC ERROR Line %d] Redeclaration of variable '%s'.\n", line, inst->arg2);
                semanticErrors++;
                return -1;
            }
            insertSymbol((char *)inst->arg2, (char *)inst->arg1, "-", "Global", line);
            break;

        case CMD_ASSIGN:
            checkVarUsed(inst->arg1, line);
            checkExpressionVars(inst->arg2, line);
            break;

        case CMD_READ:
            checkVarUsed(inst->arg1, line);
            break;

        case CMD_PRINT:
            // Check if arg1 is string literal or expression
            if (inst->arg1[0] != '"') {
                checkExpressionVars(inst->arg1, line);
            }
            break;

        case CMD_IF:
        case CMD_WHILE:
            blockDepth++;
            checkExpressionVars(inst->arg1, line);
            break;

        case CMD_ELSE:
            if (blockDepth <= 0) {
                fprintf(stderr, "[SEMANTIC ERROR Line %d] ELSE without matching IF.\n", line);
                semanticErrors++;
                return -1;
            }
            break;

        case CMD_END_IF:
        case CMD_END_WHILE:
        case CMD_END_FOR:
            if (blockDepth <= 0) {
                fprintf(stderr, "[SEMANTIC ERROR Line %d] Unmatched block end statement.\n", line);
                semanticErrors++;
                return -1;
            }
            blockDepth--;
            break;

        case CMD_FOR:
            blockDepth++;
            // Check or auto-declare loop variable if not present
            if (findSymbol((char *)inst->arg1) == -1) {
                insertSymbol((char *)inst->arg1, "INT", "0", "Loop", line);
            } else {
                updateUsage((char *)inst->arg1, line);
            }
            checkExpressionVars(inst->arg2, line);
            checkExpressionVars(inst->arg3, line);
            break;

        default:
            break;
    }

    return 0;
}

void semanticReport()
{
    printf("\n========== SEMANTIC ANALYSIS ==========\n");
    if(semanticErrors == 0 && blockDepth == 0)
        printf("[SUCCESS] No semantic errors found. All variable usages and block scopes are valid.\n");
    else {
        if (blockDepth > 0) {
            printf("[ERROR] Unclosed block structure (missing END_IF/END_FOR/END_WHILE).\n");
            semanticErrors++;
        }
        printf("[FAILED] Total semantic errors: %d\n", semanticErrors);
    }
    printf("========================================\n");
}