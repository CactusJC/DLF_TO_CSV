#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <libdivecomputer/context.h>
#include <libdivecomputer/descriptor.h>
#include <libdivecomputer/parser.h>

typedef struct {
    unsigned int time;
    double depth;
    double temperature;
    double ppo2;
    int has_temp;
    int has_ppo2;
} sample_t;

typedef struct {
    sample_t *samples;
    size_t count;
    size_t capacity;
    double current_depth;
} sample_vector_t;

typedef struct {
    unsigned int time;
    const char *type;
    const char *name;
} event_t;

typedef struct {
    event_t *events;
    size_t count;
    size_t capacity;
} event_vector_t;

typedef struct {
    sample_vector_t *samples;
    event_vector_t *events;
} callback_data_t;

static void sample_callback(dc_sample_type_t type, const dc_sample_value_t *value, void *userdata)
{
    callback_data_t *data = (callback_data_t *)userdata;
    sample_vector_t *s_vector = data->samples;
    event_vector_t *e_vector = data->events;

    if (type == DC_SAMPLE_TIME) {
        if (s_vector->count == s_vector->capacity) {
            s_vector->capacity = (s_vector->capacity == 0) ? 128 : s_vector->capacity * 2;
            sample_t *tmp = (sample_t *)realloc(s_vector->samples, s_vector->capacity * sizeof(sample_t));
            if (tmp == NULL) {
                fprintf(stderr, "PARSER_ERR: realloc failed for samples\n");
                exit(3);
            }
            s_vector->samples = tmp;
        }

        sample_t *sample = &s_vector->samples[s_vector->count++];
        memset(sample, 0, sizeof(sample_t));
        sample->time = value->time / 1000;
        sample->depth = s_vector->current_depth;

    } else if (s_vector->count > 0) {
        sample_t *sample = &s_vector->samples[s_vector->count - 1];
        if (type == DC_SAMPLE_DEPTH) {
            sample->depth = value->depth;
            s_vector->current_depth = value->depth;
        } else if (type == DC_SAMPLE_TEMPERATURE) {
            sample->temperature = value->temperature;
            sample->has_temp = 1;
        } else if (type == DC_SAMPLE_PPO2) {
            sample->ppo2 = value->ppo2.value;
            sample->has_ppo2 = 1;
        } else if (type == DC_SAMPLE_EVENT) {
            if (e_vector->count == e_vector->capacity) {
                e_vector->capacity = (e_vector->capacity == 0) ? 16 : e_vector->capacity * 2;
                event_t *tmp = (event_t *)realloc(e_vector->events, e_vector->capacity * sizeof(event_t));
                if (tmp == NULL) {
                    fprintf(stderr, "PARSER_ERR: realloc failed for events\n");
                    exit(3);
                }
                e_vector->events = tmp;
            }
            event_t *event = &e_vector->events[e_vector->count++];
            event->time = value->event.time;
            event->type = "marker"; // Placeholder
            // event->name = value->event.name; // This field does not exist.
        }
    }
}

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <dlf_file>\n", argv[0]);
        return 1;
    }

    const char *filepath = argv[1];
    FILE *file = NULL;
    unsigned char *buffer = NULL;
    long filesize;
    dc_context_t *context = NULL;
    dc_parser_t *parser = NULL;
    dc_descriptor_t *descriptor = NULL;
    sample_vector_t s_vector = {0};
    event_vector_t e_vector = {0};
    int rc = 0;

    file = fopen(filepath, "rb");
    if (!file) {
        fprintf(stderr, "PARSER_ERR: Cannot open file: %s\n", filepath);
        rc = 2;
        goto cleanup;
    }

    fseek(file, 0, SEEK_END);
    filesize = ftell(file);
    fseek(file, 0, SEEK_SET);

    buffer = (unsigned char *)malloc(filesize);
    if (!buffer) {
        fprintf(stderr, "PARSER_ERR: Cannot allocate memory\n");
        rc = 3;
        goto cleanup;
    }

    if (fread(buffer, 1, filesize, file) != filesize) {
        fprintf(stderr, "PARSER_ERR: Cannot read file: %s\n", filepath);
        rc = 4;
        goto cleanup;
    }
    // File is read, we can close it.
    fclose(file);
    file = NULL;

    dc_status_t status;

    status = dc_context_new(&context);
    if (status != DC_STATUS_SUCCESS) {
        fprintf(stderr, "PARSER_ERR: dc_context_new failed with status %d\n", status);
        rc = 5;
        goto cleanup;
    }

    dc_iterator_t *iterator;
    dc_descriptor_iterator_new(&iterator, context);
    while (dc_iterator_next(iterator, &descriptor) == DC_STATUS_SUCCESS) {
        if (strcmp(dc_descriptor_get_vendor(descriptor), "Divesoft") == 0 &&
            strcmp(dc_descriptor_get_product(descriptor), "Freedom") == 0) {
            break;
        }
        dc_descriptor_free(descriptor);
        descriptor = NULL;
    }
    dc_iterator_free(iterator);

    if (descriptor == NULL) {
        fprintf(stderr, "PARSER_ERR: Divesoft Freedom descriptor not found\n");
        rc = 6;
        goto cleanup;
    }

    status = dc_parser_new2(&parser, context, descriptor, buffer, filesize);
    if (status != DC_STATUS_SUCCESS) {
        fprintf(stderr, "PARSER_ERR: dc_parser_new2 failed with status %d\n", status);
        rc = 7;
        goto cleanup;
    }

    // JSON output
    printf("{\n");
    printf("  \"meta\": {\n");
    printf("    \"source_file\": \"%s\"", filepath);

    dc_datetime_t datetime;
    if (dc_parser_get_datetime(parser, &datetime) == DC_STATUS_SUCCESS) {
        printf(",\n    \"date\": \"%04d-%02d-%02d\",\n", datetime.year, datetime.month, datetime.day);
        printf("    \"time\": \"%02d:%02d:%02d\"", datetime.hour, datetime.minute, datetime.second);
    }

    unsigned int duration;
    if (dc_parser_get_field(parser, DC_FIELD_DIVETIME, 0, &duration) == DC_STATUS_SUCCESS) {
        printf(",\n    \"duration\": \"%u:%02u min\"", duration / 60, duration % 60);
    }

    printf(",\n    \"otu\": null,\n    \"cns\": null");

    printf(",\n    \"divecomputer\": { \"model\": \"%s\", \"serial\": \"%s\" }",
           dc_descriptor_get_product(descriptor), "not-implemented");

    dc_tank_t tank;
    if (dc_parser_get_field(parser, DC_FIELD_TANK, 0, &tank) == DC_STATUS_SUCCESS) {
        printf(",\n    \"cylinder\": { \"size_l\": %.1f, \"work_pressure_bar\": %.1f }",
               tank.volume, tank.workpressure);
    } else {
        printf(",\n    \"cylinder\": { \"size_l\": null, \"work_pressure_bar\": null }");
    }

    printf("\n  },\n");

    callback_data_t cb_data = { &s_vector, &e_vector };
    dc_parser_samples_foreach(parser, sample_callback, &cb_data);

    printf("  \"samples\": [\n");
    for (size_t i = 0; i < s_vector.count; ++i) {
        sample_t *sample = &s_vector.samples[i];
        printf("    { \"index\": %zu, \"time\": \"%u:%02u\", \"depth\": %.2f",
               i, sample->time / 60, sample->time % 60, sample->depth);
        if (sample->has_temp) {
             printf(", \"temperature\": %.1f", sample->temperature);
        }
        if (sample->has_ppo2) {
            printf(", \"ppo2\": %.2f", sample->ppo2);
        }
        printf(", \"event\": null }");
        if (i < s_vector.count - 1) {
            printf(",\n");
        } else {
            printf("\n");
        }
    }
    printf("  ]");

    printf(",\n  \"events\": [\n");
    for (size_t i = 0; i < e_vector.count; ++i) {
        event_t *event = &e_vector.events[i];
        printf("    { \"time\": \"%u:%02u\", \"type\": \"%s\", \"note\": \"%s\" }",
               event->time / 60, event->time % 60, event->type, event->name);
        if (i < e_vector.count - 1) {
            printf(",\n");
        } else {
            printf("\n");
        }
    }
    printf("  ]\n");
    printf("}\n");

cleanup:
    if (s_vector.samples)
        free(s_vector.samples);
    if (e_vector.events)
        free(e_vector.events);
    if (parser)
        dc_parser_destroy(parser);
    if (descriptor)
        dc_descriptor_free(descriptor);
    if (context)
        dc_context_free(context);
    if (buffer)
        free(buffer);
    if (file)
        fclose(file);

    return rc;
}