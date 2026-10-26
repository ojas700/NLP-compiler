#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include "codegen_c.h"
#include "symbol_table.h"

static const char *getCType(const char *ilType) {
    if (strcmp(ilType, "INT") == 0) return "int";
    if (strcmp(ilType, "FLOAT") == 0) return "float";
    if (strcmp(ilType, "CHAR") == 0) return "char";
    return "int";
}

static const char *getScanfFormat(const char *name) {
    int idx = findSymbol((char *)name);
    if (idx != -1) {
        if (strcmp(symbolTable[idx].type, "FLOAT") == 0) return "%f";
        if (strcmp(symbolTable[idx].type, "CHAR") == 0) return " %c";
    }
    return "%d";
}

static const char *getPrintfFormat(const char *name) {
    int idx = findSymbol((char *)name);
    if (idx != -1) {
        if (strcmp(symbolTable[idx].type, "FLOAT") == 0) return "%.2f\\n";
        if (strcmp(symbolTable[idx].type, "CHAR") == 0) return "%c\\n";
    }
    return "%d\\n";
}

int generateCCode(const ILInstruction instructions[], int count, const char *output_filename)
{
    FILE *f = fopen(output_filename, "w");
    if (!f) {
        fprintf(stderr, "Error opening %s for writing\n", output_filename);
        return -1;
    }

    fprintf(f, "/* NLP COMPILER - Deterministic Generated C */\n");
    fprintf(f, "#include <stdio.h>\n");
    fprintf(f, "#include <stdlib.h>\n\n");
    fprintf(f, "int main() {\n");
    fprintf(f, "    setvbuf(stdout, NULL, _IONBF, 0);\n"); // Unbuffered stdout for live interactive stdin/stdout

    int indent = 1;
    #define PRINT_INDENT() for(int k = 0; k < indent; k++) fprintf(f, "    ")

    for (int i = 0; i < count; i++) {
        const ILInstruction *inst = &instructions[i];

        switch (inst->type) {
            case CMD_DECLARE:
                PRINT_INDENT();
                fprintf(f, "%s %s = 0;\n", getCType(inst->arg1), inst->arg2);
                break;

            case CMD_ASSIGN:
                PRINT_INDENT();
                fprintf(f, "%s = %s;\n", inst->arg1, inst->arg2);
                break;

            case CMD_READ: {
                PRINT_INDENT();
                fprintf(f, "printf(\"Enter %%s: \", \"%s\"); fflush(stdout);\n", inst->arg1);
                PRINT_INDENT();
                fprintf(f, "if (scanf(\"%s\", &%s) != 1) { return 0; }\n", getScanfFormat(inst->arg1), inst->arg1);
                break;
            }

            case CMD_PRINT: {
                PRINT_INDENT();
                if (inst->arg1[0] == '"') {
                    // String literal
                    fprintf(f, "printf(\"%%s\\n\", %s);\n", inst->arg1);
                } else {
                    int idx = findSymbol((char *)inst->arg1);
                    if (idx != -1) {
                        fprintf(f, "printf(\"%s: %s\", %s);\n", inst->arg1, getPrintfFormat(inst->arg1), inst->arg1);
                    } else {
                        // Might be expression or number
                        fprintf(f, "printf(\"Result: %%d\\n\", (int)(%s));\n", inst->arg1);
                    }
                }
                break;
            }

            case CMD_IF:
                PRINT_INDENT();
                fprintf(f, "if (%s) {\n", inst->arg1);
                indent++;
                break;

            case CMD_ELSE:
                if (indent > 1) indent--;
                PRINT_INDENT();
                fprintf(f, "} else {\n");
                indent++;
                break;

            case CMD_END_IF:
                if (indent > 1) indent--;
                PRINT_INDENT();
                fprintf(f, "}\n");
                break;

            case CMD_WHILE:
                PRINT_INDENT();
                fprintf(f, "while (%s) {\n", inst->arg1);
                indent++;
                break;

            case CMD_END_WHILE:
                if (indent > 1) indent--;
                PRINT_INDENT();
                fprintf(f, "}\n");
                break;

            case CMD_FOR:
                PRINT_INDENT();
                fprintf(f, "for (%s = %s; %s <= %s; %s++) {\n",
                        inst->arg1, inst->arg2, inst->arg1, inst->arg3, inst->arg1);
                indent++;
                break;

            case CMD_END_FOR:
                if (indent > 1) indent--;
                PRINT_INDENT();
                fprintf(f, "}\n");
                break;

            default:
                break;
        }
    }

    fprintf(f, "\n    return 0;\n");
    fprintf(f, "}\n");

    fclose(f);
    return 0;
}
