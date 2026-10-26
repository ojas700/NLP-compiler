#ifndef COMPILER_COMMON_H
#define COMPILER_COMMON_H

#define MAX_CODE_LINES 500
#define MAX_LINE_LEN 256
#define MAX_NAME_LEN 64
#define MAX_EXPR_LEN 128

typedef enum {
    CMD_UNKNOWN = 0,
    CMD_DECLARE,
    CMD_ASSIGN,
    CMD_READ,
    CMD_PRINT,
    CMD_IF,
    CMD_ELSE,
    CMD_END_IF,
    CMD_WHILE,
    CMD_END_WHILE,
    CMD_FOR,
    CMD_END_FOR
} CommandType;

typedef struct {
    int line_number;
    CommandType type;
    char raw[MAX_LINE_LEN];
    char arg1[MAX_NAME_LEN];  /* e.g. INT or var_name */
    char arg2[MAX_NAME_LEN];  /* e.g. var_name or expr */
    char arg3[MAX_EXPR_LEN];  /* e.g. expr or range start/end */
} ILInstruction;

#endif
