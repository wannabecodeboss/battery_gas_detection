#include "main.h"
#include <string.h>
#include <stdio.h>

//----------------------------------------
// HANDLES
//----------------------------------------
UART_HandleTypeDef huart1;
ADC_HandleTypeDef hadc1;

//----------------------------------------
// SAMPLING CONTROL
//----------------------------------------
uint8_t sampling = 0;

uint32_t start_time = 0;
uint32_t lastSample = 0;

#define SAMPLE_INTERVAL 10   // ms

//----------------------------------------
// UART RX BUFFER
//----------------------------------------
uint8_t rx_data;
char rx_buffer[32];
uint8_t rx_index = 0;

//----------------------------------------
// FUNCTION DECLARATIONS
//----------------------------------------
uint32_t read_adc(uint32_t channel);
void process_command(char *cmd);

//----------------------------------------
// UART INTERRUPT CALLBACK
//----------------------------------------
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART1)
    {
        if (rx_data == '\n' || rx_data == '\r')
        {
            rx_buffer[rx_index] = '\0';
            process_command(rx_buffer);
            rx_index = 0;
        }
        else
        {
            if (rx_index < sizeof(rx_buffer) - 1)
            {
                rx_buffer[rx_index++] = rx_data;
            }
        }

        // Restart interrupt
        HAL_UART_Receive_IT(&huart1, &rx_data, 1);
    }
}

//----------------------------------------
// PROCESS COMMANDS
//----------------------------------------
void process_command(char *cmd)
{
    if (strcmp(cmd, "PING") == 0)
    {
        char *msg = "STM32\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
    }

    else if (strcmp(cmd, "START") == 0)
    {
        sampling = 1;
        start_time = HAL_GetTick();
        lastSample = HAL_GetTick();

        char *msg = "START\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
    }

    else if (strcmp(cmd, "STOP") == 0)
    {
        sampling = 0;

        char *msg = "STOP\r\n";
        HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
    }
}

//----------------------------------------
// ADC READ FUNCTION
//----------------------------------------
uint32_t read_adc(uint32_t channel)
{
    ADC_ChannelConfTypeDef sConfig = {0};

    sConfig.Channel = channel;
    sConfig.Rank = ADC_REGULAR_RANK_1;
    sConfig.SamplingTime = ADC_SAMPLETIME_15CYCLES;

    HAL_ADC_ConfigChannel(&hadc1, &sConfig);

    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);

    return HAL_ADC_GetValue(&hadc1);
}

//----------------------------------------
// MAIN
//----------------------------------------
int main(void)
{
    HAL_Init();
    SystemClock_Config();

    MX_GPIO_Init();
    MX_USART1_UART_Init();
    MX_ADC1_Init();

    // Start UART interrupt
    HAL_UART_Receive_IT(&huart1, &rx_data, 1);

    char msg[64];

    while (1)
    {
        uint32_t now = HAL_GetTick();

        if (sampling && (now - lastSample >= SAMPLE_INTERVAL))
        {
            lastSample = now;

            uint32_t t = now - start_time;

            uint32_t h2  = read_adc(ADC_CHANNEL_0);
            uint32_t co2 = read_adc(ADC_CHANNEL_1);
            uint32_t co  = read_adc(ADC_CHANNEL_2);

            // format: time(ms),h2,co2,co
            sprintf(msg, "%lu,%lu,%lu,%lu\r\n", t, h2, co2, co);

            HAL_UART_Transmit(&huart1, (uint8_t*)msg, strlen(msg), HAL_MAX_DELAY);
        }
    }
}
