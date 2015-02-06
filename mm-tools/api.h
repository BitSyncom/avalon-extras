#ifndef __API_H__
#define __API_H__

#include "auc.h"

/* MBOOT API */
void mm_detect(void);
void mboot(void);

/* MM API */
void mm_coretest(uint16_t testcores, uint16_t freq[], uint16_t voltage);
void set_radiator_mode();

#endif /* __API_H__ */
